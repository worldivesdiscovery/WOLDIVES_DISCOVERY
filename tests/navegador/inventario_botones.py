#!/usr/bin/env python3
"""Inventario automático de botones, enlaces y formularios de WORLDIVES DISCOVERY, por pantalla y por papel, probados
uno a uno en un navegador real (Chromium, escritorio 1366×900, es-ES).

Para cada papel (visitante, buceador, centro propietario, instructor del centro, freelance y administración):
- arranca un servidor con una copia NUEVA de la base de demostración (lo que se pulse en un papel no llega a otro);
- abre cada pantalla a la que llega ese papel: las rutas públicas, las páginas de la cuenta, cada pestaña del panel y
  cada subpestaña (las pantallas se descubren siguiendo los enlaces internos y las pestañas, como haría una persona);
- enumera lo que se puede pulsar (a[href], button, [role=button], input submit/button, select y formularios) y lo
  prueba aislado: recarga la pantalla, lo pulsa (un formulario se envía VACÍO), cancela cualquier confirm()/prompt()
  y mira qué pasa durante ~1,5 s: navegación, ventanas, avisos, validación, peticiones al servidor y errores.

Resultados: «Funciona», «Depende de clave pendiente», «Sin efecto», «Error», «Desactivado (correcto)»,
«Desactivado (sin explicación)» y «No probado» (solo cuando el elemento desaparece al recargar).
Los enlaces externos no se abren: se comprueba que la dirección es https válida. «Cerrar sesión», «Borrar mi cuenta»,
«Restaurar demo» y parecidos se prueban al final del papel y solo hasta la confirmación, que se cancela.

    python3 tests/navegador/inventario_botones.py [--demo BASE.sqlite3] [--roles visitante,buceador,...]
                                                  [--paralelo 3] [--max-pantallas 150] [--salida docs/auditoria]

Escribe docs/auditoria/botones.md (resumen e inventario) y docs/auditoria/botones.json (datos en bruto).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import traceback
from collections import Counter, deque
from pathlib import Path
from urllib.parse import urlparse, unquote

HERE = Path(__file__).resolve().parent

# An element whose centre lies outside a box that clips it (overflow hidden, e.g. a map marker just off the edge of the
# map) cannot be seen, so another element «on top» of that point does not hide it from anybody.
CLIPPED_JS = """el => { const r = el.getBoundingClientRect(), x = r.left + r.width / 2, y = r.top + r.height / 2;
  for (let a = el.parentElement; a; a = a.parentElement) { const cs = getComputedStyle(a);
    if (/hidden|clip|auto|scroll/.test(cs.overflowX + ' ' + cs.overflowY)) { const b = a.getBoundingClientRect();
      if (x < b.left || x > b.right || y < b.top || y > b.bottom) return true; } }
  return false; }"""
ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE), str(ROOT / 'tests')]

DEMO_PW = 'Worldives-Prueba-2026'          # docs/pruebas/README-PRUEBAS.md
ADMIN_PW = 'Inventario-Admin-2026'
DESK = {'width': 1366, 'height': 900}

ROLES = {   # clave: (nombre en el informe, usuario, contraseña)
    'visitante': ('Visitante (sin sesión)', None, None),
    'buceador': ('Buceador (buzo.prueba)', 'buzo.prueba', DEMO_PW),
    'centro': ('Centro propietario (centro.prueba)', 'centro.prueba', DEMO_PW),
    'instructor': ('Instructor del centro (instructor.prueba)', 'instructor.prueba', DEMO_PW),
    'freelance': ('Freelance (freelance.prueba)', 'freelance.prueba', DEMO_PW),
    'admin': ('Administración (cuenta creada para la prueba)', 'admin', ADMIN_PW),
}
STATUSES = ['Funciona', 'Depende de clave pendiente', 'Sin efecto', 'Error', 'Desactivado (correcto)',
            'Desactivado (sin explicación)', 'No probado']

PUBLIC_SEEDS = ['#/', '#/explorar', '#/puntos', '#/centros', '#/tipos', '#/experiencias', '#/top10', '#/planes',
                '#/como-funcionan-los-puntos', '#/legal']
VISITOR_SEEDS = ['#/login', '#/registro', '#/recuperar']
ACCOUNT_SEEDS = ['#/area', '#/cuenta', '#/logbook', '#/recompensas', '#/mis-puntos', '#/admin']
PRIVATE = {'area', 'cuenta', 'logbook', 'recompensas', 'mis-puntos', 'admin', 'reserva', 'manifiesto', 'barco', 'mi-plan', 'equipo',
           'salida-cancelada', 'pago-ok', 'verificarreserva', 'checkin/*', 'r/*'}     # account and panel; the rest (booking flow included) is public
NO_FOLLOW = {'eliminar-cuenta', 'restablecer', 'verificar-email', 'setup', 'verificacion', 'baja'}   # token links from emails
INSTANCES = {'reserva': 8}          # booking detail: one per state (the buttons change with the state)
GROUP_MIN, GROUP_TESTED = 3, 2      # lists of identical elements: 3 or more → the first 2 are tested
CHROME_ZONES = {'cabecera', 'pie', 'menu', 'flotante', 'cookies'}
ZONE_NAMES = {'cabecera': 'cabecera', 'pie': 'pie de página', 'menu': 'menú del panel', 'flotante': 'flotante',
              'cookies': 'aviso de cookies', 'contenido': 'contenido', 'ventana': 'ventana'}

LOGOUT_RX = re.compile(r'cerrar (la )?sesi[oó]n|^salir$|log ?out|desconectar', re.I)
DANGER_RX = re.compile(r'borrar mi cuenta|cerrar mi cuenta|eliminar (mi |la )?cuenta|borrar (la )?cuenta|cerrar la cuenta|'
                       r'darme de baja|restaurar (la )?demo|reabrir (mi |la )?cuenta', re.I)
RAW_RX = re.compile(r'TypeError|ReferenceError|SyntaxError|RangeError|is not defined|is not a function|Cannot read propert|'
                    r'Cannot set propert|Unexpected token|Traceback|Internal Server Error|\[object Object\]|\bundefined\b|\bNaN\b|'
                    r'sqlite3?\.|OperationalError|IntegrityError|KeyError|AttributeError|ValueError|Exception\b|Failed to fetch|'
                    r'NetworkError|^Error \d{3}$|Respuesta no válida del servidor|Endpoint no encontrado')
SCREEN_RAW_RX = re.compile(r'\bundefined\b|\bNaN\b|\[object Object\]|TypeError|ReferenceError|Traceback|Internal Server Error|Invalid Date|'
                           r'\bnull\b(?! *[-–] )')
JS_ERR_RX = re.compile(r'TypeError|ReferenceError|SyntaxError|RangeError|is not defined|is not a function|Cannot read|'
                       r'Cannot set|Uncaught|undefined')
KEY_RX = [
    ('Stripe', re.compile(r'(cobros|pagos?) online[^.]{0,80}(no est[aá]n?|todav[ií]a no|a[uú]n no|desactivad|sin configurar)|'
                          r'pago seguro[^.]{0,40}(no est[aá]|a[uú]n no|todav[ií]a no)|clave de stripe|'
                          r'stripe[^.]{0,40}(no est[aá]|sin configurar|no configurad|desactivad)|falta instalar[^.]{0,40}stripe', re.I)),
    ('WhatsApp (Meta)', re.compile(r'whatsapp[^.]{0,60}(no est[aá] activad|todav[ií]a no|sin configurar|no configurad|no disponible)', re.I)),
    ('Correo (SMTP)', re.compile(r'smtp|correo corporativo|env[ií]o pendiente de configurar|cuando configures el (correo|servidor)', re.I)),
    ('ArcGIS (satélite)', re.compile(r'arcgis|sat[eé]lite no disponible|vista sat[eé]lite[^.]{0,40}(no|desactivad)', re.I)),
    ('Firebase (push)', re.compile(r'firebase|notificaciones push[^.]{0,40}(no|desactivad)', re.I)),
    ('Wikimedia Commons', re.compile(r'wikimedia|commons[^.]{0,30}(no|inténtalo)', re.I)),
    ('servicio sin configurar', re.compile(r'no est[aá]n? configurad|sin configurar|pendiente de configurar|falta la clave|añade la clave', re.I)),
]
from helpers import PNG_BYTES as PNG1  # noqa: E402  (a real image: uploads are opened and checked)


VALIDATION_ES = [('Please fill out this field', 'campo obligatorio'), ('Please select an item in the list', 'elige una opción de la lista'),
                 ('Please check this box', 'casilla obligatoria'), ('Please select one of these options', 'elige una opción'),
                 ("Please include an '@'", 'correo sin @'), ('Please enter an email address', 'correo no válido'), ('Please enter a URL', 'dirección web no válida'),
                 ('Please enter a number', 'número no válido'), ('Value must be greater than or equal to', 'valor por debajo del mínimo'),
                 ('Value must be less than or equal to', 'valor por encima del máximo'), ('Please lengthen this text', 'texto demasiado corto'),
                 ('Please match the requested format', 'formato no válido'), ('Please select a file', 'falta el archivo')]


def es_validation(msg):
    for en, es in VALIDATION_ES:
        if msg.startswith(en):
            return es
    return msg


def known_routes() -> set[str]:
    """Route names of the SPA router (const routes={...} in world-dives-v8.js), read at run time."""
    src = (ROOT / 'public' / 'js' / 'world-dives-v8.js').read_text(encoding='utf-8')
    m = re.search(r'const routes=\{(.*?)\};', src, re.S)
    names = set(re.findall(r"(?:^|,)\s*'?([\w-]+)'?\s*:", m.group(1))) if m else set()
    return names | {'legal', 'checkin', 'r', 'promo'}


# ------------------------------------------------------------------------------------------------ page-side helpers
INIT_JS = r"""
(() => {
  try { if (!sessionStorage.getItem('wdinv-cookies')) localStorage.setItem('wd_cookie_notice', String(Date.now())); else localStorage.removeItem('wd_cookie_notice'); } catch (e) {}
  window.print = () => { window.__wdinvPrints = (window.__wdinvPrints || 0) + 1; };
  const STATE = /^(active|is-on|is-active|show|shown|open|is-open|selected|is-selected|current|is-current|on|is-closing|loading|is-loading|hover|is-hover|focus|focused|is-focus|dirty|is-dirty)$/;
  const txt = s => (s || '').replace(/\s+/g, ' ').trim();
  const path = n => { const parts = []; while (n && n.nodeType === 1 && n !== document.body && n !== document.documentElement && parts.length < 14) {
      let p = n.tagName.toLowerCase(); if (n.id && !/^\d/.test(n.id)) p += '#' + n.id;
      const c = [...n.classList].filter(x => !STATE.test(x)).slice(0, 3); if (c.length) p += '.' + c.join('.');
      parts.unshift(p); n = n.parentElement; } return parts.join('>'); };
  const S = window.__wdinv = { log: null, noisy: [], path, txt };
  const cap = (arr, v) => { if (arr.length < 150) arr.push(v); };
  S.mut = m => {
    const L = S.log; if (!L) return;
    const t = m.target.nodeType === 1 ? m.target : m.target.parentElement; if (!t) return;
    if (t.closest && t.closest('#toast')) { const tt = txt(document.getElementById('toast')?.innerText); if (tt && !L.toasts.includes(tt)) L.toasts.push(tt); return; }
    if (m.type === 'attributes' && (m.attributeName === 'data-wdinv' || m.attributeName === 'data-wdinv-target')) return;
    const p = path(t); if (S.noisy.some(x => p === x || p.startsWith(x + '>'))) return;
    if (m.type === 'childList') {
      m.addedNodes.forEach(n => {
        if (n.nodeType === 1) { if (n.id === 'toast') return;
          cap(L.added, { path: p, tag: n.tagName.toLowerCase(), cls: [...n.classList].join('.'), id: n.id || '',
            text: txt(n.innerText || n.textContent).slice(0, 240),
            modal: !!(n.matches && n.matches('.wd-modal,[role=dialog],dialog,.modal-backdrop,[aria-modal=true]')) }); }
        else if (n.nodeType === 3 && txt(n.textContent)) cap(L.text, { path: p, text: txt(n.textContent).slice(0, 240) });
      });
      L.removed += m.removedNodes.length;
    } else if (m.type === 'attributes') {
      const nv = t.getAttribute(m.attributeName); if (nv === m.oldValue) return;
      if (m.attributeName === 'style' && (p.includes('leaflet') )) { L.mapMoves++; return; }
      cap(L.attrs, { path: p, attr: m.attributeName, old: m.oldValue == null ? null : m.oldValue.slice(0, 80), new: nv == null ? null : nv.slice(0, 80), self: t.hasAttribute('data-wdinv-target') });
    } else if (m.type === 'characterData') cap(L.text, { path: p, text: txt(m.target.textContent).slice(0, 240) });
    L.n++;
  };
  S.arm = noisy => {
    S.noisy = noisy || [];
    S.log = { n: 0, added: [], attrs: [], text: [], toasts: [], invalid: [], scroll: [], removed: 0, mapMoves: 0 };
    S.href0 = location.href; S.scroll0 = [scrollX, scrollY]; S.prints0 = window.__wdinvPrints || 0;
    S.textLen0 = document.body ? document.body.innerText.length : 0;
    S.modals0 = document.querySelectorAll('.wd-modal,[role=dialog],dialog[open]').length;
    S.app0 = (document.querySelector('#app')?.innerText || '').slice(0, 400);
    S.err0 = /No se ha podido abrir esta secci[oó]n/.test(document.querySelector('#app')?.innerText || '');
    S.focus0 = document.activeElement;
    S.vals0 = new Map([...document.querySelectorAll('input,select,textarea')].filter(f => f.type !== 'hidden').map(f => [f, f.type === 'checkbox' || f.type === 'radio' ? String(f.checked) : f.value]));
    if (S.obs) S.obs.disconnect();
    S.obs = new MutationObserver(ms => { for (const m of ms) S.mut(m); });
    S.obs.observe(document.documentElement, { subtree: true, childList: true, attributes: true, characterData: true, attributeOldValue: true });
    if (!S.listening) { S.listening = true;
      document.addEventListener('invalid', e => { const L = S.log; if (!L) return; const f = e.target; const lab = (f.labels && f.labels[0] && txt(f.labels[0].innerText)) || f.getAttribute('aria-label') || f.name || f.id || f.type;
        cap(L.invalid, { field: lab.slice(0, 60), msg: f.validationMessage || '' }); }, true);
      document.addEventListener('scroll', e => { const L = S.log; if (!L) return; const t = e.target === document ? 'documento' : path(e.target);
        if (S.noisy.some(x => t === x || t.startsWith(x + '>'))) return; if (!L.scroll.includes(t)) cap(L.scroll, t); }, true);
    }
  };
  S.peek = () => { const L = S.log || { n: 0, toasts: [], invalid: [], scroll: [] };
    return { n: L.n + L.toasts.length + L.invalid.length + L.scroll.length, href: location.href, prints: (window.__wdinvPrints || 0) - (S.prints0 || 0) }; };
  S.report = () => {
    const L = S.log || { n: 0, added: [], attrs: [], text: [], toasts: [], invalid: [], scroll: [], removed: 0, mapMoves: 0 };
    if (S.obs) S.obs.disconnect();
    const modals = [...document.querySelectorAll('.wd-modal,[role=dialog],dialog[open]')].filter(m => m.checkVisibility ? m.checkVisibility() : true)
      .map(m => txt((m.querySelector('h1,h2,h3,legend') || {}).innerText || m.getAttribute('aria-label') || '').slice(0, 100));
    const app = document.querySelector('#app');
    const appText = app ? app.innerText : '';
    const errScreen = !S.err0 && /No se ha podido abrir esta secci[oó]n/.test(appText) ? txt(appText).slice(0, 300) : '';
    const tst = document.getElementById('toast'); const toastNow = tst && tst.classList.contains('show') ? txt(tst.innerText) : '';
    if (toastNow && !L.toasts.includes(toastNow)) L.toasts.push(toastNow);
    return { log: L, href0: S.href0, href: location.href, scroll0: S.scroll0, scroll: [scrollX, scrollY], prints: (window.__wdinvPrints || 0) - (S.prints0 || 0),
      textLen0: S.textLen0, textLen: document.body ? document.body.innerText.length : 0, modals0: S.modals0, modals, errScreen,
      appChanged: (app?.innerText || '').slice(0, 400) !== S.app0,
      focus: (() => { const f = document.activeElement; if (!f || f === S.focus0 || f === document.body || f.hasAttribute('data-wdinv-target') || f.closest('[data-wdinv-target]')) return '';
        return path(f).split('>').slice(-1)[0]; })(),
      focusNow: document.activeElement ? path(document.activeElement).split('>').slice(-1)[0] : '',
      values: [...(S.vals0 || new Map()).entries()].filter(([f, v]) => f.isConnected && !f.hasAttribute('data-wdinv-target') && (f.type === 'checkbox' || f.type === 'radio' ? String(f.checked) : f.value) !== v)
        .slice(0, 3).map(([f, v]) => ({ field: txt((f.labels && f.labels[0] && f.labels[0].innerText) || f.getAttribute('aria-label') || f.name || f.id).slice(0, 50), old: String(v).slice(0, 40),
          new: String(f.type === 'checkbox' || f.type === 'radio' ? f.checked : f.value).slice(0, 40) })) };
  };
})();
"""

ENUM_JS = r"""
(arg) => {
  const light = !!(arg && arg.light);
  const find = arg && arg.qs ? arg : null;     // quick search of one element (by its selector, signature and position)
  const txt = s => (s || '').replace(/\s+/g, ' ').trim();
  const STATE = /^(active|is-on|is-active|show|shown|open|is-open|selected|is-selected|current|is-current|on|is-closing|loading|is-loading|hover|is-hover|focus|focused|is-focus|dirty|is-dirty|disabled|is-disabled)$/;
  const vis = el => { try { if (el.checkVisibility && !el.checkVisibility({ checkOpacity: true, checkVisibilityCSS: true })) return false; } catch (e) {}
    const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const zoneOf = el => el.closest('#ck-bar') ? 'cookies' : el.closest('.wd-modal,[role=dialog],dialog,[aria-modal=true]') ? 'ventana'
    : el.closest('.site-header') ? 'cabecera' : el.closest('.site-footer') ? 'pie' : el.closest('.cb-sidebar,.provider-tabs,.acc-tabs') ? 'menu'
    : el.closest('#app') ? 'contenido' : 'flotante';
  const labelOf = el => {
    const aria = txt(el.getAttribute('aria-label'));
    if (el.tagName === 'FORM') {
      const h = el.querySelector('h1,h2,h3,h4,legend');
      const sub = [...el.querySelectorAll('button,input[type=submit]')].find(b => (b.type || 'submit') === 'submit');
      let near = ''; const box = el.closest('section,.card,.acc-card,.cb-module,.auth-card,.wd-modal-card,div'); const hh = box && box.querySelector('h1,h2,h3');
      if (hh && !el.contains(hh)) near = txt(hh.innerText);
      return aria || (h && txt(h.innerText)) || near || (sub && txt(sub.innerText || sub.value)) || el.id || 'formulario';
    }
    if (el.tagName === 'SELECT') { const l = el.labels && el.labels[0];
      const td = el.closest('td'); let col = '';
      if (td && !aria && !l) { const th = td.closest('table')?.querySelectorAll('thead th')[td.cellIndex]; const row = td.parentElement?.cells[0];
        col = txt(th?.innerText) + (row && row !== td ? ' · ' + txt(row.innerText).slice(0, 40) : ''); }
      return aria || (l && txt(l.innerText)) || col || txt(el.title) || el.id || el.name || txt(el.options[el.selectedIndex]?.text) || 'desplegable'; }
    let t = txt(el.innerText);
    if (t.length > 70) { const h = el.querySelector('h1,h2,h3,h4,strong,b'); if (h && txt(h.innerText)) t = txt(h.innerText); }
    const img = el.querySelector('img[alt]');
    return aria || t || txt(el.title) || txt(el.value) || (img && txt(img.alt)) || txt(el.getAttribute('href')) || ('[' + [...el.classList].join('.') + ']');
  };
  const explain = el => {
    const parts = []; if (el.title) parts.push(txt(el.title));
    const d = el.getAttribute('aria-describedby'); if (d) d.split(/\s+/).forEach(id => { const x = document.getElementById(id); if (x) parts.push(txt(x.innerText)); });
    // Nearby hints, up to the card or form that holds the button; an instruction («elige…», «te faltan…») is preferred.
    const WHY = /\bpara\b|cuando|hasta|necesit|primero|no hay|todavía|aún|\bsin\b|falta|requiere|añade|elige|marca|acepta|completa|disponible|activa|configura|escribe|selecciona|sube|toca|pulsa|indica|no admite|no se puede|no puedes|solo |mínimo|máximo/i;
    let p = el.parentElement, near = '';
    for (let i = 0; i < 6 && p; i++, p = p.parentElement) {
      const t = [...p.querySelectorAll('small,.hint,.muted,.help,.notice,.modal-help,.svc-hint,.note,.empty,.acc-empty,label,legend,p')].filter(x => !x.contains(el) && vis(x)).map(x => txt(x.innerText)).filter(Boolean);
      const good = t.find(x => WHY.test(x) && x.length < 200);
      if (good) { parts.push(good); break; }
      if (!near && t.length) near = t.slice(0, 2).join(' · ');
      if (p.matches('form,.card,.acc-card,.cb-panel,.wd-modal-card,section,aside,article')) break;
    }
    if (!parts.length && near) parts.push(near);
    return parts.join(' · ').slice(0, 220);
  };
  const SEL = 'a[href], button, [role=button], input[type=submit], input[type=button], input[type=reset], input[type=image], select, form';
  const out = []; let i = 0;
  document.querySelectorAll('[data-wdinv],[data-wdinv-target]').forEach(e => { e.removeAttribute('data-wdinv'); e.removeAttribute('data-wdinv-target'); });
  let nodes;
  if (find) { try { nodes = document.querySelectorAll(find.qs); } catch (e) { return []; } } else nodes = document.querySelectorAll(SEL);
  for (const el of nodes) {
    if (el.closest('#toast')) continue;
    const tag = el.tagName.toLowerCase();
    const visible = tag === 'form' ? [...el.elements].some(vis) : vis(el);
    if (!visible) continue;
    el.setAttribute('data-wdinv', String(i));
    const label = labelOf(el).slice(0, 110);
    const cls = [...el.classList].filter(c => !STATE.test(c)).sort().join('.');
    const dataA = [...el.attributes].filter(a => a.name.startsWith('data-') && a.name !== 'data-wdinv' && a.name !== 'data-wdinv-target');
    const data = dataA.map(a => a.name + '=' + a.value).sort().join('&');
    const href = el.getAttribute('href') || '';
    const type = (el.getAttribute('type') || (tag === 'button' ? 'submit' : '')).toLowerCase();
    const role = el.getAttribute('role') || '';
    const zone = zoneOf(el);
    const sig = [tag, type, role, label, el.id || '', href, el.getAttribute('name') || '', data, cls].join('|');
    const r = { i, tag, type, role, label, zone, sig, loose: sig.replace(/\d+/g, '#'), cls, href, id: el.id || '',
      pressed: el.getAttribute('aria-pressed') === 'true' || el.getAttribute('aria-selected') === 'true' || (el.getAttribute('aria-current') || 'false') !== 'false'
        || /(^|\s)(active|is-on|is-active|selected|is-selected|current)(\s|$)/.test(el.getAttribute('class') || '') };
    if (!light) {
      let qs = tag + (el.id ? '#' + CSS.escape(el.id) : '') + (href ? `[href="${CSS.escape(href)}"]` : '')
        + dataA.slice(0, 3).map(a => `[${a.name}="${CSS.escape(a.value)}"]`).join('');
      if (qs === tag) qs += [...el.classList].filter(c => !STATE.test(c)).slice(0, 2).map(c => '.' + CSS.escape(c)).join('');
      r.qs = qs;
      const marker = el.classList.contains('leaflet-marker-icon') || el.classList.contains('leaflet-interactive');
      const digitHref = /\d/.test(href);
      const anchor = /^#(?!\/)./.test(href);    // in-page anchors (table of contents): one list
      const dated = dataA.some(a => /^\d{4}-\d{2}(-\d{2})?/.test(a.value));   // calendar days and departures: one list
      const off = !!(el.disabled || el.getAttribute('aria-disabled') === 'true');
      // dates and numbers do not make two buttons different («Mié, 14 oct 16:00 6 libres» and «Jue, 15 oct 16:00 6 libres»)
      const DATEW = /\b(lun|mar|mi[eé]|jue|vie|s[aá]b|dom)[a-zé]*\.?,|\d+\s*(de\s+)?(ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)[a-z]*\.?/gi;
      const glabel = label.replace(DATEW, 'D').replace(/\d+/g, '#');
      r.group = [tag, cls, dataA.map(a => a.name).sort().join(','), anchor ? '#ancla' : href.replace(/\d+/g, '#').replace(/=[^&#]*/g, '='),
                 (digitHref || marker || anchor || dated) ? '' : glabel, zone, off ? 'off' : ''].join('|');
      r.disabled = !!(el.disabled || el.getAttribute('aria-disabled') === 'true' || (tag === 'a' && el.classList.contains('disabled')) || el.closest('fieldset[disabled]'));
      r.explain = r.disabled ? explain(el) : '';
      r.target = el.getAttribute('target') || '';
      r.download = el.hasAttribute('download');
      r.navlike = zone === 'menu' || el.matches('[data-cbtab],[data-tab],[data-go],[data-sub],[data-pt],[role=tab],.cb-go,.tab,.pr-tab,.svc-tab,.bk-view,.cb-nav');
      r.abs = tag === 'a' ? el.href : '';
      r.inForm = !!(el.form);
      r.isSubmit = !!(el.form) && ((tag === 'button' && el.type === 'submit') || (tag === 'input' && (el.type === 'submit' || el.type === 'image')));
      if (tag === 'select') { r.options = el.options.length; r.selected = el.selectedIndex; r.multiple = el.multiple;
        let p = el.parentElement; r.applyBtn = '';
        for (let k = 0; k < 4 && p && !r.applyBtn; k++, p = p.parentElement) {
          const b = [...p.querySelectorAll('button,input[type=submit],input[type=button]')].find(b => !b.contains(el) && vis(b) && /guardar|aplicar|cambiar|actualizar|buscar|filtrar|enviar|confirmar|añadir|crear|ver|asignar|mover|generar|aprobar|verificar|validar|publicar|save|apply/i.test(b.innerText || b.value || ''));
          if (b) r.applyBtn = txt(b.innerText || b.value).slice(0, 40);
          if (p.matches('tr,li,form,fieldset,section,.wd-modal-card')) break;
        } }
      if (tag === 'form') { const f = [...el.elements].filter(x => vis(x) && /^(INPUT|TEXTAREA|SELECT)$/.test(x.tagName) && !/^(submit|button|reset|image|hidden)$/.test(x.type));
        r.fields = f.length; r.required = f.filter(x => x.required).length;
        const sub = [...el.elements].find(b => (b.tagName === 'BUTTON' && b.type === 'submit') || (b.tagName === 'INPUT' && /^(submit|image)$/.test(b.type)));
        r.submitLabel = sub ? txt(sub.innerText || sub.value) : ''; r.submitDisabled = !!(sub && sub.disabled); r.novalidate = el.noValidate;
        r.text = txt(el.innerText).slice(0, 300); }
      r.danger = '';
    }
    out.push(r); i++;
  }
  if (find) {
    for (const f of ['sig', 'loose']) { const c = out.filter(x => x[f] === find[f]); if (c.length > find.occ) return [c[find.occ]]; }
    return [];
  }
  return out;
}
"""

SCREEN_JS = r"""
() => {
  const txt = s => (s || '').replace(/\s+/g, ' ').trim();
  const vis = el => { try { if (el.checkVisibility && !el.checkVisibility({ checkOpacity: true, checkVisibilityCSS: true })) return false; } catch (e) {}
    const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const h = document.querySelector('#app h1') || document.querySelector('#app h2');
  const navs = [...document.querySelectorAll('.cb-nav[data-cbtab], .provider-tabs .tab[data-tab]')].filter(vis);
  const activeNav = navs.find(b => b.classList.contains('active'));
  const isOn = b => b.getAttribute('aria-selected') === 'true' || b.getAttribute('aria-pressed') === 'true' || /(^|\s)(active|is-on|is-active|selected)(\s|$)/.test(b.className);
  const subs = [];
  for (const b of document.querySelectorAll('[role=tablist] button, [role=tablist] [role=tab], [role=tablist] a')) {
    if (!b.closest('#app') || b.closest('.acc-tabs,.cb-sidebar,.provider-tabs')) continue;
    if (!vis(b)) continue;
    const tl = b.closest('[role=tablist]');
    const dataA = [...b.attributes].filter(a => a.name.startsWith('data-') && !a.name.startsWith('data-wdinv'));
    let sel = null;
    if (dataA.length) {
      sel = b.tagName.toLowerCase() + dataA.map(a => `[${a.name}="${CSS.escape(a.value)}"]`).join('');
      const c0 = tl && [...tl.classList][0]; if (c0) sel = '.' + CSS.escape(c0) + ' ' + sel;
      if (document.querySelectorAll(sel).length !== 1) sel = null;
    }
    if (!sel) { const c0 = tl && [...tl.classList][0]; const k = [...tl.children].indexOf(b) + 1;
      sel = (c0 ? '.' + CSS.escape(c0) : '[role=tablist]') + ' > :nth-child(' + k + ')'; if (document.querySelectorAll(sel).length !== 1) sel = null; }
    subs.push({ label: txt(b.innerText).replace(/\s*\d+$/, '').slice(0, 60), active: isOn(b), sel, list: tl ? txt(tl.getAttribute('aria-label') || [...tl.classList].join('.')) : '' });
  }
  const links = [...document.querySelectorAll('a[href^="#/"]')].map(a => a.getAttribute('href'));
  return { h1: h ? txt(h.innerText).slice(0, 90) : '', title: document.title,
    nav: activeNav ? { tab: activeNav.dataset.cbtab || activeNav.dataset.tab, label: txt(activeNav.innerText).replace(/\s*\d+$/, '') } : null,
    navs: navs.map(b => ({ tab: b.dataset.cbtab || b.dataset.tab, label: txt(b.innerText).replace(/\s*\d+$/, ''), active: b.classList.contains('active') })),
    subs, links, hash: location.hash,
    errScreen: /No se ha podido abrir esta secci[oó]n/.test(document.querySelector('#app')?.innerText || '') ? txt(document.querySelector('#app').innerText).slice(0, 300) : '',
    appText: (document.querySelector('#app')?.innerText || '').slice(0, 60000) };
}
"""

LOCK_JS = r"""
(el) => {
  // A control that does not answer to the mouse (pointer-events: none), usually a step of a form that opens later.
  if (getComputedStyle(el).pointerEvents !== 'none') return null;
  const txt = s => (s || '').replace(/\s+/g, ' ').trim();
  let dim = false;
  for (let x = el; x && x.id !== 'app' && x !== document.body; x = x.parentElement) {
    const cs = getComputedStyle(x); if (+cs.opacity < 1 || (cs.filter && cs.filter !== 'none')) { dim = true; break; } }
  const WHY = /primero|antes de|elige|selecciona|completa|necesit|falta|cuando|hasta/i;
  let why = '';
  for (let a = el.parentElement; a && a.id !== 'app' && !why; a = a.parentElement) {
    for (const c of [a, a.previousElementSibling]) {
      if (!c) continue;
      const t = [...c.querySelectorAll('p,small,span,.hint,.muted,h3,h4,label')].map(x => txt(x.innerText)).find(x => WHY.test(x) && x.length < 160);
      if (t) { why = t; break; }
    }
  }
  return { dim, why };
}
"""

FORM_CLEAR_JS = r"""
(form) => {
  const vis = el => { try { return el.checkVisibility ? el.checkVisibility() : true; } catch (e) { return true; } };
  let n = 0;
  for (const f of form.elements) {
    if (!vis(f)) continue;
    if (f.tagName === 'TEXTAREA' || (f.tagName === 'INPUT' && !/^(submit|button|reset|image|hidden|checkbox|radio|file|range|color)$/.test(f.type))) {
      if (f.readOnly) continue; f.value = ''; f.dispatchEvent(new Event('input', { bubbles: true })); f.dispatchEvent(new Event('change', { bubbles: true })); n++; }
    else if (f.tagName === 'INPUT' && f.type === 'checkbox' && f.required) { f.checked = false; n++; }
    else if (f.tagName === 'SELECT' && f.required) { const e = [...f.options].findIndex(o => o.value === ''); if (e >= 0) { f.selectedIndex = e; n++; } }
  }
  const sub = [...form.elements].find(b => (b.tagName === 'BUTTON' && b.type === 'submit') || (b.tagName === 'INPUT' && /^(submit|image)$/.test(b.type)))
    || (form.id ? document.querySelector(`button[form="${form.id}"]`) : null);
  if (sub) sub.setAttribute('data-wdinv-target', '1');
  return { cleared: n, hasSubmit: !!sub, submitDisabled: !!(sub && sub.disabled) };
}
"""


# ------------------------------------------------------------------------------------------------ the crawler of one role
class RoleCrawler:
    def __init__(self, role: str, demo: Path, max_screens: int, log=print, part='todo'):
        self.role, self.demo, self.max_screens, self.log, self.part = role, demo, max_screens, log, part
        self.role_name, self.user, self.password = ROLES[role]
        self.routes = known_routes()
        self.records: list[dict] = []
        self.screens: list[dict] = []
        self.seen_keys: set[str] = set()
        self.queued: set[str] = set()
        self.instances: Counter = Counter()
        self.sub_done: set[tuple] = set()
        self.chrome_done: set[str] = set()
        self.tested_base: dict[str, set] = {}
        self.deferred: list[tuple] = []
        self.link_done: dict[str, dict] = {}
        self.server_restarts = 0
        self.fresh_restarts = 0
        self.writes = 0
        self.srv = None
        self.noisy: list[str] = []
        self.dirty = True
        self.cur_screen = None

    # ---------------------------------------------------------------- server and session
    def start_server(self):
        from helpers import Server
        if self.srv:
            self.srv.stop()
        env = {'WOD_ADMIN_TOTP_REQUIRED': '0', 'WOD_PAYMENTS_TOTP_REQUIRED': '0', 'HTTPS_PROXY': '', 'HTTP_PROXY': '', 'https_proxy': '', 'http_proxy': '', 'ALL_PROXY': '', 'all_proxy': ''}
        self.srv = Server(env, seed=self.demo).start()
        self.base = self.srv.base
        self.writes = 0
        if self.role == 'admin':
            r = self.srv.run_cli('--create-admin', '--email', 'admin@inventario.example.org', '--username', 'admin', '--name', 'Admin Inventario',
                                 env={'WOD_ADMIN_PASSWORD': ADMIN_PW})
            if r.returncode != 0:
                raise RuntimeError('No se ha podido crear la administración: ' + r.stdout + r.stderr)

    def new_context(self):
        if getattr(self, 'ctx', None):
            try:
                self.ctx.close()
            except Exception:
                pass
        self.ctx = self.browser.new_context(viewport=DESK, locale='es-ES', timezone_id='Europe/Madrid', accept_downloads=True,
                                            permissions=['clipboard-read', 'clipboard-write', 'geolocation'],
                                            geolocation={'latitude': 38.7920, 'longitude': 0.1810})   # Xàbia: «usar mi ubicación» works as for a person who allows it
        self.ctx.add_init_script(INIT_JS)
        self.page = page = self.ctx.new_page()
        page.set_default_timeout(10000)
        self.inflight, self.capture, self.reqmap = {}, None, {}
        self.ev = {'dialogs': [], 'downloads': [], 'popups': [], 'files': 0, 'pageerrors': [], 'console': [], 'loads': 0, 'blocked': []}
        self.ctx.route('**/*', self._route)     # the context (not only the page): new tabs are routed too
        page.on('request', self._on_request)
        page.on('response', self._on_response)
        page.on('requestfinished', lambda r: self.inflight.pop(r, None))
        page.on('requestfailed', self._on_failed)
        page.on('dialog', self._on_dialog)
        page.on('download', lambda d: self.ev['downloads'].append(d.suggested_filename))
        page.on('popup', lambda p: self.ev['popups'].append(p))
        page.on('filechooser', lambda f: self.ev.__setitem__('files', self.ev['files'] + 1))
        page.on('pageerror', lambda e: self.ev['pageerrors'].append(str(e).strip().split('\n')[0][:300]))
        page.on('console', self._on_console)
        page.on('domcontentloaded', lambda p: self.ev.__setitem__('loads', self.ev['loads'] + 1))

    def _route(self, route):
        from e2e_markers import ADMIN_REASON
        req = route.request
        url = req.url
        if url.startswith(self.base) or url.startswith('data:') or url.startswith('blob:'):
            return route.continue_(headers={**req.headers, 'x-admin-reason': ADMIN_REASON})
        self.ev['blocked'].append(url[:160])
        if req.resource_type == 'image':
            return route.fulfill(body=PNG1, content_type='image/png')
        return route.abort()

    def _same(self, url):
        return url.startswith(self.base)

    def _on_request(self, req):
        if not self._same(req.url):
            return
        rec = {'method': req.method, 'path': req.url[len(self.base):][:160], 'type': req.resource_type, 'status': None, 'error': '', 'nav': req.is_navigation_request()}
        self.reqmap[req] = rec
        if self.capture is not None:
            self.capture.append(rec)
        if req.resource_type in ('document', 'script', 'stylesheet', 'fetch', 'xhr'):
            self.inflight[req] = time.time()

    def _on_response(self, resp):
        rec = self.reqmap.get(resp.request)
        if rec is not None:
            rec['status'] = resp.status
            if resp.status >= 400 and self.capture is not None:
                rec['_resp'] = resp

    def _on_failed(self, req):
        self.inflight.pop(req, None)
        rec = self.reqmap.get(req)
        if rec is not None:
            rec['failure'] = req.failure or 'falló'

    def _on_dialog(self, d):
        self.ev['dialogs'].append({'type': d.type, 'message': (d.message or '')[:240]})
        try:
            d.accept() if d.type == 'beforeunload' else d.dismiss()
        except Exception:
            pass

    def _on_console(self, msg):
        if msg.type != 'error':
            return
        t = (msg.text or '').strip().split('\n')[0]     # the message, without the stack trace
        if 'Failed to load resource' in t or 'net::ERR' in t:
            return
        self.ev['console'].append(t[:300])

    def wait_ready(self, max_s=10.0, quiet_s=0.25):
        t0 = time.time()
        quiet = None
        while True:
            self.page.wait_for_timeout(50)
            now = time.time()
            for r, ts in list(self.inflight.items()):
                if now - ts > 12:
                    self.inflight.pop(r, None)
            if not self.inflight:
                quiet = quiet or now
                if now - quiet >= quiet_s:
                    break
            else:
                quiet = None
            if now - t0 > max_s:
                break
        self.page.wait_for_timeout(80)

    def goto(self, route):
        page = self.page
        self.reqmap = {}
        self.nav_n = getattr(self, 'nav_n', 0) + 1
        page.goto(f'{self.base}/?lang=es&_={self.nav_n}{route}', wait_until='domcontentloaded', timeout=20000)
        self.wait_ready()

    def session_ok(self) -> bool:
        if not self.user:
            return True
        try:
            r = self.ctx.request.get(self.base + '/api/me', timeout=10000)
            d = r.json()
        except Exception:
            return False
        u = (d or {}).get('user') or {}
        if u.get('username') != self.user or d.get('account_closed'):
            return False
        if getattr(self, 'me0', None) and (u.get('role'), u.get('center_id')) != self.me0:
            return False
        return True

    def login(self):
        if not self.user:
            return
        page = self.page
        self.goto('#/login')
        page.fill('#login', self.user)
        page.fill('#password', self.password)
        page.click('#login-form button[type=submit]')
        for _ in range(60):
            page.wait_for_timeout(150)
            if 'login' not in page.url.split('#')[-1]:
                break
        self.wait_ready()
        if not self.session_ok() and not getattr(self, 'me0', None):
            # API login as a fallback (the browser login is the one tried first; a failure is reported).
            r = self.ctx.request.post(self.base + '/api/auth/login', data={'login': self.user, 'password': self.password}, headers={'Origin': self.base})
            self.log(f'  ! inicio de sesión en el navegador fallido; por la API: {r.status}')
        d = self.ctx.request.get(self.base + '/api/me').json()
        u = d.get('user') or {}
        if u.get('username') != self.user:
            raise RuntimeError(f'No se ha podido iniciar sesión como {self.user}: {d}')
        if not getattr(self, 'me0', None):
            self.me0 = (u.get('role'), u.get('center_id'))
        self.dirty = True

    def recover(self, why):
        """The previous click closed the session or changed the account: log in again, or start from a fresh copy."""
        self.log(f'  · recuperación ({why})')
        try:
            self.login()
            if self.session_ok():
                return 'se vuelve a iniciar sesión'
        except Exception:
            pass
        self.recover_fresh()
        return 'servidor reiniciado con una copia nueva de la base'

    def recover_fresh(self):
        self.server_restarts += 1
        self.start_server()
        self.new_context()
        self.login()

    # ---------------------------------------------------------------- screens
    def route_name(self, hash_):
        h = (hash_ or '#/').lstrip('#').lstrip('/')
        name, _, qs = h.partition('?')
        for p in ('checkin/', 'r/', 'promo/'):
            if name.startswith(p):
                return p + '*', qs
        return name or 'home', qs

    def open_screen(self, sc):
        self.goto(sc['route'])
        for sel in sc.get('clicks', []):
            loc = self.page.locator(sel).first
            loc.click(timeout=5000)
            self.wait_ready()
        self.page.mouse.move(2, 2)
        self.dirty = False
        self.cur_screen = sc['id'] if 'id' in sc else None
        self.screen_url = self.page.url
        self.screen_n = self.count_elements()

    def screen_key(self, info, sc):
        name, qs = self.route_name(info['hash'])
        key = name
        if name in INSTANCES:
            m = re.search(r'(?:^|&)id=(\d+)', qs)
            if m and self.instances[name] < INSTANCES[name]:
                key += '#' + m.group(1)
        if info.get('nav'):
            key += '|tab=' + info['nav']['tab']
        act = sorted({s['label'] for s in info['subs'] if s['active'] and s['label']})
        if sc.get('clicks') and act:
            key += '|' + ','.join(re.sub(r'\d+', '#', a) for a in act)
        return key

    def enqueue(self, queue, route, clicks=None, parent=None, label=None):
        name, qs = self.route_name(route)
        if name.split('/')[0] in NO_FOLLOW or not self.in_part(name):
            return
        params = [kv.partition('=') for kv in qs.split('&') if kv]
        k = route if (name in INSTANCES) else name + ''.join(f'&{a}={v}' for a, _, v in params if a in ('tab', 'sub', 'pt'))
        k = k + '|' + '>'.join(clicks or [])
        if k in self.queued:
            return
        self.queued.add(k)
        queue.append({'route': route, 'clicks': list(clicks or []), 'parent': parent, 'via': label})

    def in_part(self, name):
        if self.part == 'todo' or not self.user:
            return True
        return (name in PRIVATE) == (self.part == 'privada')

    def baseline(self):
        page = self.page
        page.evaluate('() => window.__wdinv.arm([])')
        page.wait_for_timeout(1100)
        rep = page.evaluate('() => window.__wdinv.report()')
        L = rep['log']
        noisy = {x['path'] for x in L['added']} | {x['path'] for x in L['attrs']} | {x['path'] for x in L['text']} | set(L['scroll'])
        if L['toasts']:
            noisy.add('div#toast')
        return sorted(noisy)

    def enumerate(self, light=False):
        return self.page.evaluate(ENUM_JS, {'light': light})

    # ---------------------------------------------------------------- run
    def run(self):
        from playwright.sync_api import sync_playwright
        from e2e_markers import chromium
        self.start_server()
        t0 = time.time()
        with sync_playwright() as p:
            self.browser = chromium(p)
            self.new_context()
            self.login()
            queue = deque()
            seeds = PUBLIC_SEEDS + (VISITOR_SEEDS if not self.user else ACCOUNT_SEEDS)
            if self.user:   # the panel first: it is the main screen of professionals
                seeds = ['#/admin'] + [s for s in seeds if s != '#/admin'] if self.role in ('centro', 'instructor', 'freelance', 'admin') else seeds
            for s in seeds:
                self.enqueue(queue, s)
            if not self.user:
                queue.append({'route': '#/', 'clicks': [], 'cookies': True, 'via': 'aviso de cookies'})
            if self.part == 'privada':       # the header and the footer are tested by the public part
                self.chrome_done.add('*')
            while queue and len(self.screens) < self.max_screens:
                sc = queue.popleft()
                try:
                    self.process_screen(sc, queue)
                except Exception as ex:
                    self.log(f'  ! pantalla {sc["route"]} {sc.get("clicks")}: {ex.__class__.__name__}: {str(ex)[:200]}')
                    self.screens.append({'route': sc['route'], 'clicks': sc.get('clicks', []), 'key': 'fallo:' + sc['route'], 'title': sc['route'],
                                         'issues': [f'No se ha podido abrir para el inventario: {str(ex)[:200]}'], 'elements': 0})
                    self.dirty = True
                    if not self.session_ok():
                        self.recover('tras un fallo al abrir la pantalla')
            if queue:
                self.log(f'  ! se alcanza el máximo de {self.max_screens} pantallas; quedan {len(queue)} sin abrir')
            self.left_out = [q['route'] for q in queue]
            self.process_deferred()
            try:
                self.ctx.close()
                self.browser.close()
            except Exception:
                pass
        self.seconds = round(time.time() - t0)
        self.srv.stop()

    def process_screen(self, sc, queue):
        page = self.page
        if sc.get('cookies'):
            page.goto(self.base + '/?lang=es#/', wait_until='domcontentloaded')
            page.evaluate("() => { sessionStorage.setItem('wdinv-cookies', '1'); localStorage.removeItem('wd_cookie_notice'); }")
        self.ev['pageerrors'].clear(); self.ev['console'].clear()
        self.capture = []
        t0 = time.time()
        self.open_screen(sc)
        load_s = time.time() - t0
        net = self.capture
        self.capture = None
        info = page.evaluate(SCREEN_JS)
        self.screen_text = re.sub(r'\s+', ' ', info.get('appText', ''))
        key = self.screen_key(info, sc) + ('|cookies' if sc.get('cookies') else '')
        if key in self.seen_keys:
            return
        name, _ = self.route_name(info['hash'])
        if not self.in_part(name):      # e.g. #/login sends a logged-in person to #/cuenta: that screen belongs to the other part
            return
        if name in INSTANCES and '#' in key.split('|')[0]:
            self.instances[name] += 1
        self.seen_keys.add(key)
        issues, notes = [], []
        for e in self.ev['pageerrors']:
            issues.append('Error de JavaScript al abrir: ' + e)
        for e in self.ev['console']:
            if JS_ERR_RX.search(e):
                issues.append('Error en la consola al abrir: ' + e)
        for r in net:
            if r['status'] and r['status'] >= 500:
                issues.append(f"El servidor responde {r['status']} a {r['method']} {r['path']}")
            elif r['status'] == 404 and r['type'] in ('image', 'stylesheet', 'script', 'font', 'media'):
                issues.append(f"Recurso que no existe (404): {r['path'].split('?')[0]}")
            elif r['status'] and r['status'] >= 400 and r['type'] in ('fetch', 'xhr'):
                notes.append(f"{r['method']} {r['path'].split('?')[0][:80]} → {r['status']}")
        if info['errScreen']:
            issues.append('Muestra «No se ha podido abrir esta sección»: ' + info['errScreen'][:200])
        for line in info.get('appText', '').split('\n'):
            m = SCREEN_RAW_RX.search(line)
            if m:
                issues.append(f'Texto técnico a la vista: «{line.strip()[:140]}»')
                break
        screen_keys = []
        for line in ('' if name.startswith('legal') else info.get('appText', '')).split('\n'):
            for n, rx in KEY_RX:
                if rx.search(line) and len(line) < 400:
                    screen_keys.append(f'{n}: «{line.strip()[:200]}»')
                    break
        screen_keys = list(dict.fromkeys(screen_keys))[:4]
        if name not in self.routes and name.split('/')[0] not in self.routes:
            issues.append(f'Ruta desconocida para el router: #{info["hash"][1:]} (se muestra la portada)')
        title = info['h1'] or info['title']
        if info.get('nav'):
            title = (info['h1'] + ' · ' if info['h1'] else '') + info['nav']['label']
        if sc.get('clicks'):
            title += ' › ' + ' › '.join(sc.get('labels', []) or ['subpestaña'])
        if sc.get('cookies'):
            title += ' (aviso de cookies)'
        screen = {'id': len(self.screens), 'key': key, 'route': info['hash'] or sc['route'], 'requested': sc['route'], 'clicks': sc.get('clicks', []),
                  'labels': sc.get('labels', []), 'title': title, 'issues': issues, 'keys': screen_keys, 'notes': list(dict.fromkeys(notes))[:6], 'load_s': round(load_s, 2), 'via': sc.get('via'), 'cookies': bool(sc.get('cookies'))}
        if info['hash'] and self.route_name(info['hash'])[0] != self.route_name(sc['route'])[0]:
            screen['redirect'] = f"{sc['route']} → {info['hash']}"
        self.screens.append(screen)
        sc['id'] = screen['id']
        self.log(f"- [{len(self.screens):3d}] {title[:60]}  ({screen['route']}{' + ' + str(len(sc.get('clicks', []))) + ' clic' if sc.get('clicks') else ''})")
        # discovery: internal links, panel tabs, sub-tabs
        if not sc.get('cookies'):
            for h in info['links']:
                self.enqueue(queue, h)
            if self.route_name(info['hash'])[0] == 'admin':
                for n in info['navs']:
                    if not n['active']:
                        self.enqueue(queue, '#/admin?tab=' + n['tab'], label=n['label'])
            base_key = key.split('|')[0] + ('|tab=' + info['nav']['tab'] if info.get('nav') else '')
            for s in info['subs']:
                if s['active'] and s['sel']:
                    self.sub_done.add((base_key, s['sel']))     # the tab already open is this same screen
            for s in info['subs']:
                if s['active'] or not s['sel']:
                    continue
                k = (base_key, s['sel'])
                if k in self.sub_done:
                    continue
                self.sub_done.add(k)
                route = info['hash'] or sc['route']
                queue.appendleft({'route': route, 'clicks': sc.get('clicks', []) + [s['sel']], 'labels': sc.get('labels', []) + [s['label']], 'via': 'subpestaña'})
        # the elements
        self.noisy = self.baseline()
        els = self.enumerate()
        screen['elements'] = len(els)
        self.dirty = True
        base_key = key.split('|')[0] + ('|tab=' + info['nav']['tab'] if info.get('nav') else '')
        tested = self.tested_base.setdefault(base_key, set())
        groups = Counter(e['group'] for e in els)
        gseen, occ = Counter(), Counter()
        first_of_group = {}
        todo = []
        for e in els:
            e['occ'] = occ[e['sig']]
            occ[e['sig']] += 1
            if e['isSubmit'] and e['inForm']:
                continue     # tested with its form
            if e['zone'] in CHROME_ZONES and not sc.get('cookies'):
                if e['sig'] in self.chrome_done or ('*' in self.chrome_done and e['zone'] in ('cabecera', 'pie', 'cookies')):
                    continue
                self.chrome_done.add(e['sig'])
            elif sc.get('cookies') and e['zone'] != 'cookies':
                continue
            if sc.get('clicks') and e['sig'] in tested:
                continue
            tested.add(e['sig'])
            if groups[e['group']] >= GROUP_MIN:
                gseen[e['group']] += 1
                n_test = 1 if e['tag'] == 'a' else GROUP_TESTED
                if gseen[e['group']] > n_test:
                    first_of_group[e['group']]['repeated'] = groups[e['group']] - n_test
                    continue
                first_of_group.setdefault(e['group'], e)
            lab = e['label'] + ' ' + (e.get('submitLabel') or '')
            if LOGOUT_RX.search(e['label']) or 'logout' in e['href']:
                self.deferred.append((dict(sc), screen, e, 'logout'))
                continue
            if DANGER_RX.search(lab) or (e['tag'] == 'form' and DANGER_RX.search(e.get('text', '')[:120])):
                self.deferred.append((dict(sc), screen, e, 'danger'))
                continue
            todo.append(e)
        for e in todo:
            h = e['href'] if e['tag'] == 'a' else ''
            if h.startswith('#/') and h in self.link_done and not e.get('disabled'):
                first = self.link_done[h]     # same internal link already clicked in this role: same behaviour
                rec = {**first, 'screen': screen['id'], 'screen_title': screen['title'], 'route': screen['route'], 'label': e['label'],
                       'zone': e['zone'], 'repeated': e.get('repeated', 0), 'copied': True, 'evidence': {},
                       'detail': f"Mismo enlace ({h[:60]}) que «{first['label'][:40]}» en «{first['screen_title'][:40]}»: {first['detail']}"[:600]}
                self.records.append(rec)
                continue
            rec = self.test_element(sc, screen, e)
            self.records.append(rec)
            if h.startswith('#/') and rec['detail'].startswith('Abre '):     # only a plain navigation can be reused for the same link
                self.link_done.setdefault(h, rec)
        if sc.get('cookies'):
            page.evaluate("() => sessionStorage.removeItem('wdinv-cookies')")

    def process_deferred(self):
        if not self.deferred:
            return
        self.log(f'- al final: {len(self.deferred)} elementos de cierre de sesión o borrado')
        for kind in ('danger', 'logout'):
            for sc, screen, e, k in self.deferred:
                if k != kind:
                    continue
                if not self.session_ok():
                    self.recover('antes de un elemento aplazado')
                rec = self.test_element(sc, screen, e)
                rec['detail'] = ('[probado al final del papel] ' + rec['detail']).strip()
                self.records.append(rec)
                self.dirty = True

    # ---------------------------------------------------------------- one element
    def kind_of(self, e):
        if e['tag'] == 'form':
            return 'Formulario'
        if e['tag'] == 'select':
            return 'Desplegable'
        if e['tag'] == 'a':
            ext = self.is_external(e)
            return 'Enlace externo' if ext else 'Enlace'
        if e['tag'] == 'input':
            return f"Botón (input {e['type']})"
        if e['tag'] == 'button':
            return 'Botón'
        return f"Elemento {e['tag']} (role=button)"

    def is_external(self, e):
        href = e['href'].strip()
        if re.match(r'^(mailto|tel|sms|whatsapp|geo):', href, re.I):
            return True
        if re.match(r'^https?://', href, re.I) and not re.match(r'^http://(127\.0\.0\.1|localhost)(:\d+)?(/|$)', href):
            return True     # (the test servers run on 127.0.0.1; their port changes when a fresh copy is started)
        return False

    def test_element(self, sc, screen, e):
        rec = {'role': self.role, 'screen': screen['id'], 'screen_title': screen['title'], 'route': screen['route'], 'label': e['label'],
               'kind': self.kind_of(e), 'tag': e['tag'], 'zone': e['zone'], 'href': e['href'], 'repeated': e.get('repeated', 0),
               'result': '', 'detail': '', 'evidence': {}}
        t0 = time.time()
        for attempt in (1, 2):
            # «Sin efecto» and «No probado» are confirmed a second time on a fresh screen with a longer wait (3,5 s):
            # on a busy machine an answer can come late, and the inventory must not report a slow button as dead.
            self.patience = 1.5 if attempt == 1 else 3.5
            try:
                self._test(sc, e, rec)
            except Exception as ex:
                rec['result'] = 'No probado'
                rec['detail'] = f'El inventario no ha podido probarlo: {ex.__class__.__name__}: {str(ex).splitlines()[0][:200]}'
                self.dirty = True
                self.log('    ! ' + rec['detail'])
            if rec['result'] not in ('Sin efecto', 'No probado') or attempt == 2:
                break
            self.dirty = True
            first = rec['detail']
            rec.update({'result': '', 'detail': '', 'evidence': {}})
        if attempt == 2:
            rec['retried'] = True
        rec['ms'] = round((time.time() - t0) * 1000)
        if e.get('repeated'):
            rec['detail'] = (rec['detail'] + f" · hay {e['repeated']} más iguales en la lista (no se prueban todos)").strip(' ·')
        self.log(f"    {rec['ms']:5d} {rec['result'][:14]:14} {rec['kind'][:10]:10} {rec['label'][:50]:50} {rec['detail'][:110]}")
        return rec

    def _test(self, sc, e, rec):
        page = self.page
        if e.get('disabled'):
            ex = e.get('explain', '')
            keys = [n for n, rx in KEY_RX if ex and rx.search(ex)]
            if not keys and re.search(r'sat[eé]lite', e['label'], re.I):
                keys = ['ArcGIS (satélite): sin ARCGIS_API_KEY el satélite sale desactivado']
            if keys:
                rec['result'], rec['detail'] = 'Depende de clave pendiente', f'Desactivado ({keys[0]}): «{ex}»'
            elif re.match(r'(guardar|guardar cambios|actualizar)$', e['label'], re.I):
                rec['result'], rec['detail'] = 'Desactivado (correcto)', 'Desactivado hasta que se cambia algo (botón de guardar)'
            elif re.search(r'anterior|siguiente|^‹|^›|^«|^»|^<|^>|\b(menos|más)$|^[−+-]$', e['label'], re.I):
                rec['result'], rec['detail'] = 'Desactivado (correcto)', f"Desactivado: es el límite del calendario o de la lista («{e['label'][:60]}»)"
            elif re.search(r'no disponible|ocupad|complet|agotad|cerrad|pasad|llen[oa]|sin plazas|requiere|necesita|próximamente|bloquead|festivo|vacaciones', e['label'], re.I):
                rec['result'], rec['detail'] = 'Desactivado (correcto)', f"Desactivado; su propio texto dice por qué: «{e['label'][:80]}»"
            elif ex and re.search(r'\bpara\b|cuando|hasta|necesit|primero|no hay|todavía|aún|\bsin\b|falta|requiere|añade|elige|marca|acepta|completa|'
                                  r'disponible|activa|configura|escribe|selecciona|sube|toca|pulsa|indica|no admite|no se puede|no puedes|solo |mínimo|máximo', ex, re.I):
                rec['result'], rec['detail'] = 'Desactivado (correcto)', f'Desactivado; la pantalla explica: «{ex}»'
            elif ex:
                rec['result'], rec['detail'] = 'Desactivado (sin explicación)', f'Desactivado; el texto más cercano no explica por qué: «{ex[:140]}»'
            else:
                rec['result'], rec['detail'] = 'Desactivado (sin explicación)', 'Desactivado y sin texto que diga por qué'
            return
        if e['tag'] == 'a':
            href = e['href'].strip()
            if self.is_external(e):
                ok, why = self.valid_external(href)
                rec['result'], rec['detail'] = ('Funciona' if ok else 'Error'), why
                return
            if not href.startswith('#') and not href.lower().startswith('javascript:'):
                return self.check_same_origin_link(e, rec)
        # click-based test (buttons, hash links, selects, forms)
        tt = {'t0': time.time()}
        if self.dirty:
            self.open_screen(sc)
        tt['open'] = time.time()
        found = self.locate(e)
        if found is None and not self.dirty:
            self.open_screen(sc)
            found = self.locate(e)
        if found is None and self.writes and self.fresh_restarts < 40:
            # An earlier click changed the data (accepted a booking, deleted a row…) and the element is gone:
            # a fresh copy of the database brings the screen back as it was.
            self.fresh_restarts += 1
            self.log(f'    · copia nueva de la base para volver a ver «{e["label"][:40]}»')
            self.recover_fresh()
            page = self.page
            self.open_screen(sc)
            found = self.locate(e)
        if found is None:
            rec['result'], rec['detail'] = 'No probado', 'No aparece al volver a abrir la pantalla (la pantalla cambió por una prueba anterior)'
            self.dirty = True
            return
        loc = page.locator(f'[data-wdinv="{found["i"]}"]')
        e = {**e, 'pressed': found.get('pressed')}     # its state right now (some toolbars mark the active option late)
        for k in ('dialogs', 'downloads', 'popups', 'pageerrors', 'console', 'blocked'):
            self.ev[k].clear()
        self.ev['files'] = 0
        loads0 = self.ev['loads']
        url0 = page.url
        if e['tag'] != 'form':
            try:
                loc.scroll_into_view_if_needed(timeout=1000)
                loc.hover(timeout=1000)
                page.wait_for_timeout(60)
            except Exception:
                pass
        form_info = None
        how = 'clic'
        covered = ''
        if e['tag'] not in ('form',) and 'leaflet' not in (e.get('cls') or ''):
            lock = loc.evaluate(LOCK_JS)
            if lock:     # nobody can click it: it behaves as a disabled control
                if lock['why'] or lock['dim']:
                    rec['result'] = 'Desactivado (correcto)'
                    rec['detail'] = 'No responde al ratón (pointer-events: none)' + (' y se ve atenuado' if lock['dim'] else '') + (f"; la pantalla explica: «{lock['why']}»" if lock['why'] else '')
                else:
                    rec['result'], rec['detail'] = 'Desactivado (sin explicación)', 'No responde al ratón (pointer-events: none) y nada explica por qué'
                return
        page.evaluate('(n) => window.__wdinv.arm(n)', self.noisy)
        if e['tag'] != 'form':
            loc.evaluate("el => el.setAttribute('data-wdinv-target','1')")
        self.capture = []
        if e['tag'] == 'select':
            n, cur = e.get('options', 0), e.get('selected', 0)
            if n < 2:
                rec['result'], rec['detail'] = 'Sin efecto', 'Desplegable con una sola opción'
                self.capture = None
                return
            target = (cur + 1) % n
            vals = loc.evaluate('el => [...el.options].map(o => [o.value, o.disabled])')
            for j in list(range(cur + 1, n)) + list(range(0, cur)):
                if not vals[j][1] and vals[j][0] != vals[cur][0]:
                    target = j
                    break
            opt_text = loc.evaluate('(el, j) => el.options[j]?.text || el.options[j]?.value || ""', target)
            how = f'elige «{opt_text}»'[:80]
            loc.select_option(index=target, timeout=3000)
        elif e['tag'] == 'form':
            form_info = loc.evaluate(FORM_CLEAR_JS)
            page.evaluate('(n) => window.__wdinv.arm(n)', self.noisy)    # clearing the fields is not the effect
            if form_info['hasSubmit'] and not form_info['submitDisabled']:
                sub = page.locator('[data-wdinv-target="1"]').first
                try:
                    sub.click(timeout=2500)
                    how = 'se envía vacío'
                except Exception:
                    loc.evaluate('f => f.requestSubmit()')
                    how = 'se envía vacío (requestSubmit)'
            elif form_info['hasSubmit']:
                self.capture = None
                rep = page.evaluate('() => window.__wdinv.report()')
                rec['result'], rec['detail'] = 'Desactivado (correcto)', f"El botón «{e.get('submitLabel') or 'Enviar'}» está desactivado hasta completar el formulario"
                return
            else:
                loc.evaluate('f => f.requestSubmit ? f.requestSubmit() : f.submit()')
                how = 'se envía vacío (sin botón de enviar)'
        else:
            try:
                loc.click(timeout=1500)
            except Exception as ex1:
                m = re.search(r'[^\n]*intercepts pointer events', str(ex1))
                # map markers that overlap each other are normal; anything else on top of a control hides it from people
                if m and not re.search(r'leaflet-marker|marker-cluster|wd-pin|leaflet-interactive', m.group(0)) and not loc.evaluate(CLIPPED_JS):
                    covered = re.sub(r'\s+', ' ', re.sub(r'…', '', m.group(0))).replace(' intercepts pointer events', '').strip(' -')[:200]
                try:
                    loc.click(timeout=1000, force=True)
                    how = 'clic forzado (otro elemento lo tapa)'
                except Exception:
                    loc.evaluate('el => el.click()')
                    how = 'clic por JavaScript (no se puede pulsar con el ratón)'
        tt['act'] = time.time()
        obs = self.observe(url0, loads0)
        obs['covered'] = covered
        tt['obs'] = time.time()
        obs['t'] = {'open': round(tt['open'] - tt['t0'], 2), 'act': round(tt['act'] - tt['open'], 2), 'obs': round(tt['obs'] - tt['act'], 2)}
        rec['evidence'] = obs
        rec['evidence']['how'] = how
        if form_info:
            rec['evidence']['form'] = form_info
        self.classify(e, obs, rec)
        self.dirty = bool(obs['any'] or obs['net'] or e['tag'] in ('select', 'form'))
        rec['evidence'] = self.slim(obs)
        # A link that only opened another screen: «Atrás» draws the same screen again (cheaper than reloading).
        if self.dirty and not sc.get('clicks') and not sc.get('cookies') and obs.get('hash_only') and not obs['net_writes']:
            self.soft_restore(sc)
        if obs['net_writes'] or obs['left_page'] or 'login' in obs['url_after']:
            if not self.session_ok():
                rec['detail'] += ' · ' + 'cierra la sesión o cambia la cuenta: ' + self.recover('tras pulsar «' + e['label'][:40] + '»')

    def count_elements(self):
        try:
            return self.page.evaluate("() => document.querySelectorAll('a[href],button,[role=button],input,select,form').length")
        except Exception:
            return -1

    def soft_restore(self, sc):
        page = self.page
        try:
            page.go_back(wait_until='commit', timeout=5000)
            for _ in range(40):
                if page.url.split('#', 1)[-1] == self.screen_url.split('#', 1)[-1]:
                    break
                page.wait_for_timeout(25)
            self.wait_ready()
            page.mouse.move(2, 2)
            if page.url == self.screen_url and self.count_elements() == self.screen_n:
                self.dirty = False
        except Exception:
            self.dirty = True

    @staticmethod
    def slim(obs):
        rep = obs.get('rep') or {}
        L = rep.get('log') or {}
        return {'how': obs.get('how'), 'elapsed': obs.get('elapsed'), 't': obs.get('t'), 'url_after': obs.get('url_after'), 'net': obs.get('net', [])[:12],
                'dialogs': obs.get('dialogs'), 'downloads': obs.get('downloads'), 'popups': obs.get('popups'), 'files': obs.get('files'),
                'pageerrors': obs.get('pageerrors'), 'console': obs.get('console'), 'blocked': obs.get('blocked'), 'form': obs.get('form'),
                'toasts': L.get('toasts'), 'invalid': L.get('invalid'), 'modals': rep.get('modals'), 'mutations': L.get('n'),
                'added': (L.get('added') or [])[:3], 'attrs': (L.get('attrs') or [])[:3], 'scroll': (L.get('scroll') or [])[:3]}

    def locate(self, e):
        try:   # quick: only the elements that match its selector
            c = self.page.evaluate(ENUM_JS, {'light': True, 'qs': e.get('qs'), 'sig': e['sig'], 'loose': e['loose'], 'occ': e['occ']}) if e.get('qs') else []
            if c:
                return c[0]
            els = self.enumerate(light=True)
        except Exception:
            return None
        for field in ('sig', 'loose'):
            c = [x for x in els if x[field] == e[field]]
            if len(c) > e['occ']:
                return c[e['occ']]
            if c and field == 'loose':
                return c[0]
        return None

    def observe(self, url0, loads0):
        page = self.page
        t0 = time.time()
        quiet = None
        effect_at = None
        left = False
        while True:
            page.wait_for_timeout(100)
            now = time.time()
            el = now - t0
            try:
                pk = page.evaluate('() => window.__wdinv ? window.__wdinv.peek() : null')
            except Exception:
                pk = None
            if not page.url.startswith(self.base):
                left = True
            has = bool(pk and (pk['n'] or pk['prints'] or pk['href'] != url0)) or bool(self.ev['dialogs'] or self.ev['downloads'] or self.ev['popups'] or self.ev['files']) or self.ev['loads'] != loads0
            if has and effect_at is None:
                effect_at = el
            if self.inflight:
                quiet = None
            else:
                quiet = quiet or now
            q = (now - quiet) if quiet else 0
            if el >= getattr(self, 'patience', 1.5) and q >= 0.2:
                break
            if effect_at is not None and el >= 0.35 and q >= 0.2:
                break
            if el >= 6:
                break
        page.wait_for_timeout(80)
        rep = None
        try:
            if page.url.startswith(self.base):
                rep = page.evaluate('() => window.__wdinv ? window.__wdinv.report() : null')
        except Exception:
            rep = None
        net = self.capture or []
        self.capture = None
        for r in net:
            resp = r.pop('_resp', None)
            if resp is not None:
                try:
                    body = resp.text()[:400]
                    try:
                        j = json.loads(body)
                        r['error'] = str(j.get('error') or j.get('message') or '')[:240] if isinstance(j, dict) else ''
                    except Exception:
                        r['error'] = re.sub(r'<[^>]+>', ' ', body)[:160].strip()
                except Exception:
                    pass
        popups = []
        for pp in self.ev['popups']:
            u = ''
            try:
                pp.wait_for_load_state('domcontentloaded', timeout=3000)
                u = pp.url
                txt = pp.evaluate("() => document.querySelector('#app')?.innerText || document.body?.innerText || ''")[:300] if u.startswith(self.base) else ''
            except Exception:
                txt = ''
            popups.append({'url': u[:200], 'error': 'No se ha podido abrir' in txt})
            try:
                pp.close()
            except Exception:
                pass
        obs = {'rep': rep, 'net': [{k: v for k, v in r.items()} for r in net if r['type'] in ('fetch', 'xhr', 'document') or (r['status'] or 0) >= 400],
               'dialogs': list(self.ev['dialogs']), 'downloads': list(self.ev['downloads']), 'popups': popups, 'files': self.ev['files'],
               'pageerrors': list(self.ev['pageerrors']), 'console': list(self.ev['console']), 'blocked': list(self.ev['blocked'])[:5],
               'loads': self.ev['loads'] - loads0, 'url_before': url0, 'url_after': page.url, 'left_page': left or not page.url.startswith(self.base),
               'elapsed': round(time.time() - t0, 2)}
        obs['net_writes'] = any(r['method'] not in ('GET', 'HEAD') for r in obs['net'])
        self.writes += sum(1 for r in obs['net'] if r['method'] not in ('GET', 'HEAD') and (r['status'] or 999) < 400)
        obs['hash_only'] = (page.url.split('#')[0] == url0.split('#')[0] and page.url != url0 and not obs['dialogs'] and not obs['popups']
                            and not obs['downloads'] and not (self.ev['loads'] - loads0) and not obs['pageerrors'])
        L = (rep or {}).get('log') or {}
        obs['any'] = bool(L.get('n') or L.get('toasts') or L.get('invalid') or obs['dialogs'] or obs['downloads'] or obs['popups'] or obs['files']
                          or obs['loads'] or (rep and (rep['href'] != rep['href0'] or rep['prints'])) or obs['left_page'])
        return obs

    # ---------------------------------------------------------------- classification
    def classify(self, e, obs, rec):
        rep = obs['rep'] or {}
        L = rep.get('log') or {'added': [], 'attrs': [], 'text': [], 'toasts': [], 'invalid': [], 'scroll': [], 'removed': 0, 'n': 0, 'mapMoves': 0}
        effects, errors, keys, notes = [], [], [], []
        navigated = False
        fmt = lambda v: 'sin atributo' if v is None else ('vacío' if v == '' else v)
        for d in obs['dialogs']:
            effects.append({'confirm': 'Pide confirmación', 'prompt': 'Pide un dato (prompt)', 'alert': 'Muestra un aviso del navegador',
                            'beforeunload': 'Avisa al salir'}.get(d['type'], d['type']) + f" «{d['message'][:120]}»" + (' (cancelado)' if d['type'] in ('confirm', 'prompt') else ''))
        u0, u1 = obs['url_before'], obs['url_after']
        if obs['left_page'] and not u1.startswith(self.base):
            navigated = True
            ok, why = self.valid_external(u1) if u1.startswith('http') else (False, u1)
            effects.append(f'Sale de la web a {u1[:120]}')
            if not ok and not u1.startswith('chrome-error'):
                errors.append('Navega a una dirección no válida: ' + u1[:120])
            if u1.startswith('chrome-error'):
                blocked = obs['blocked'][:1]
                effects[-1] = 'Sale de la web a ' + (blocked[0] if blocked else 'otra dirección') + ' (bloqueada en la prueba)'
        elif u1 != u0 and u1.split('#')[0] != u0.split('#')[0] and u1.split('#', 1)[-1] == u0.split('#', 1)[-1]:
            navigated = True
            q0 = re.sub(r'&_=\d+', '', u0.split('#')[0]); q1 = re.sub(r'&_=\d+', '', u1.split('#')[0])
            effects.append('Vuelve a la página anterior' if q0 == q1 else 'Recarga la página con ' + u1[len(self.base):].split('#')[0][:60])
        elif u1 != u0:
            navigated = True
            h1 = '#' + u1.split('#', 1)[1] if '#' in u1 else u1[len(self.base):]
            effects.append('Abre ' + h1[:120])
            name, _ = self.route_name(h1)
            if h1.startswith('#/') and name not in self.routes and name.split('/')[0] not in self.routes:
                errors.append(f'Enlace a una ruta que no existe ({h1[:80]}): se muestra la portada')
        elif obs['loads']:
            navigated = True
            effects.append('Recarga la página')
        for dl in obs['downloads']:
            effects.append(f'Descarga «{dl}»')
        for pp in obs['popups']:
            effects.append('Abre una pestaña nueva ' + (pp['url'][len(self.base):] if pp['url'].startswith(self.base) else pp['url'])[:120])
            if pp['error']:
                errors.append('La pestaña nueva muestra «No se ha podido abrir esta sección»')
        if obs['files']:
            effects.append('Abre el selector de archivos')
        if rep.get('prints'):
            effects.append('Abre la impresión')
        new_modals = rep.get('modals', [])[:] if len(rep.get('modals', [])) > (rep.get('modals0') or 0) else []
        for m in new_modals[-1:]:
            effects.append(f'Abre la ventana «{m}»' if m else 'Abre una ventana')
        for t in L['toasts'][:2]:
            effects.append(f'Aviso: «{t[:150]}»')
        for iv in L['invalid'][:2]:
            effects.append(f"El navegador no deja enviarlo: «{iv['field']}»" + (f" ({es_validation(iv['msg'])})" if iv['msg'] else ''))
        added = [a for a in L['added'] if a['text'] or a['modal']]
        self_attrs = [a for a in L['attrs'] if a.get('self')]
        if not navigated:
            if self_attrs:
                a = self_attrs[0]
                effects.append(f"Cambia su estado ({a['attr']}: {fmt(a['old'])} → {fmt(a['new'])})")
            if added and not new_modals:
                txt = next((a['text'] for a in added if a['text']), '')
                effects.append(f'Muestra contenido nuevo ({len(L["added"])} elementos)' + (f': «{txt[:120]}»' if txt else ''))
            elif L['added'] or L['removed']:
                if not new_modals:
                    effects.append(f'Cambia la pantalla ({len(L["added"])} elementos nuevos, {L["removed"]} quitados)')
            other_attrs = [a for a in L['attrs'] if not a.get('self')]
            if other_attrs and not (L['added'] or L['removed'] or self_attrs):
                a = other_attrs[0]
                effects.append(f"Cambia {a['attr']} en {a['path'].split('>')[-1][:50]} ({fmt(a['old'])[:30]} → {fmt(a['new'])[:30]})")
            if L['text'] and not (L['added'] or L['attrs']):
                effects.append(f"Cambia el texto: «{L['text'][0]['text'][:100]}»")
            if L.get('mapMoves') and not effects:
                effects.append('Mueve o amplía el mapa')
            if L['scroll'] and not effects:
                effects.append('Desplaza ' + ('la página' if L['scroll'][0] == 'documento' else 'el contenido'))
            for v in (rep.get('values') or [])[:2]:
                effects.append(f"Cambia el valor de «{v['field']}» ({v['old'] or 'vacío'} → {v['new'] or 'vacío'})")
            if rep.get('focus') and not effects:
                effects.append(f"Lleva el foco a {rep['focus'][:60]}")
            if not effects and rep and abs((rep.get('textLen') or 0) - (rep.get('textLen0') or 0)) > 0:
                effects.append('Cambia el texto visible')
        # network
        for r in obs['net']:
            st = r['status']
            line = f"{r['method']} {r['path'].split('?')[0][:70]} → {st or r.get('failure', 'sin respuesta')}" + (f" «{r['error'][:120]}»" if r.get('error') else '')
            if st and st >= 500:
                kk = [n for n, rx in KEY_RX if r.get('error') and rx.search(r['error'])]
                (keys if kk else errors).append(f'El servidor responde {line}')
                keys.extend(kk)
            elif st in (404, 405) and ('Endpoint no encontrado' in (r.get('error') or '') or (r.get('nav') and st == 404)):
                errors.append(f'Petición a algo que no existe: {line}')
            elif st and st >= 400 and r['type'] in ('fetch', 'xhr', 'document'):
                notes.append(line)
            elif r['method'] not in ('GET', 'HEAD') and st:
                notes.append(line)
        # error texts and pending keys
        texts = L['toasts'] + [d['message'] for d in obs['dialogs']] + [r.get('error') or '' for r in obs['net']]
        # Text that appears after the click: only short messages (a whole panel or tab that is drawn is not «the answer»).
        big = sum(len(a['text']) for a in L['added']) > 600 or L['removed'] > 8
        if not navigated and not big and not e.get('navlike'):
            seen = getattr(self, 'screen_text', '')
            texts += [a['text'] for a in added[:6] if len(a['text']) < 300 and a['text'] not in seen] + \
                     [t['text'] for t in L['text'][:6] if len(t['text']) < 300 and t['text'] not in seen]
        for t in texts:
            if t and RAW_RX.search(t):
                errors.append(f'Mensaje técnico a la vista: «{t[:160]}»')
                break
        for t in texts:
            for n, rx in KEY_RX:
                if t and rx.search(t):
                    keys.append(n)
                    break
        for pe in obs['pageerrors']:
            errors.append('Error de JavaScript: ' + pe[:200])
        if obs.get('covered'):
            errors.append(f"Se ve pero otro elemento lo tapa ({obs['covered']}): con el ratón no se puede pulsar")
        for c in obs['console']:
            if JS_ERR_RX.search(c):
                errors.append('Error en la consola: ' + c[:200])
            else:
                notes.append('Consola: ' + c[:120])
        if rep.get('errScreen') and not obs['dialogs']:
            errors.append('Muestra «No se ha podido abrir esta sección»: ' + rep['errScreen'][:160])
        # verdict
        if errors:
            result = 'Error'
        elif keys:
            result = 'Depende de clave pendiente'
        elif effects:
            result = 'Funciona'
        elif any((r['status'] or 0) < 400 and r['type'] in ('fetch', 'xhr') for r in obs['net']):
            result = 'Funciona'
            effects.append('Solo una petición al servidor, sin cambio visible')
        elif 'skip-link' in (e.get('cls') or '') and 'main#app' in (rep.get('focusNow') or ''):
            result = 'Funciona'
            effects.append('El foco ya está en el contenido principal: el salto no tiene que hacer nada más (correcto)')
        elif e.get('pressed'):
            result = 'Funciona'
            effects.append('Ya estaba seleccionado: pulsarlo otra vez no cambia nada (correcto)')
        elif e['tag'] == 'select' and (e.get('inForm') or e.get('applyBtn')):
            result = 'Funciona'
            effects.append(f"Campo: el cambio se aplica al pulsar «{e.get('applyBtn') or e.get('submitLabel') or 'Guardar'}» (sin efecto inmediato, correcto)"
                           if e.get('applyBtn') else 'Campo de un formulario: el cambio se aplica al enviarlo (sin efecto inmediato, correcto)')
        elif e['tag'] == 'a' and e['href'].startswith('#/') and e['href'].rstrip('/') == (('#' + obs['url_before'].split('#', 1)[1]) if '#' in obs['url_before'] else '#/').rstrip('/'):
            result = 'Funciona'
            effects.append('Enlace a la pantalla en la que ya se está')
        else:
            result = 'Sin efecto'
            effects.append('No pasa nada visible y no se llama al servidor (observado 1,5 s y repetido con 3,5 s en la pantalla recién abierta)')
        uniq = lambda xs: list(dict.fromkeys(xs))
        parts = uniq(errors)[:3] + ([f"Clave pendiente: {', '.join(uniq(keys))}"] if keys and result != 'Funciona' else []) + uniq(effects)[:3]
        if notes and result != 'Funciona' or (notes and not effects):
            parts += uniq(notes)[:2]
        elif notes:
            parts += uniq(notes)[:1]
        how = obs.get('how') or ''
        if 'forzado' in how or 'JavaScript' in how:
            parts.append(how)
        if e['tag'] == 'form':
            parts.insert(0, 'Enviado vacío')
        rec['result'] = result
        rec['detail'] = ' · '.join(p for p in parts if p)[:600]
        rec['keys'] = uniq(keys)

    def valid_external(self, href):
        h = href.strip()
        if re.match(r'^mailto:', h, re.I):
            ok = bool(re.match(r'^mailto:[^@\s]+@[^@\s]+\.[a-z]{2,}', h, re.I))
            return ok, ('Correo ' if ok else 'Correo no válido: ') + unquote(h[7:])[:80]
        if re.match(r'^tel:', h, re.I):
            ok = bool(re.match(r'^tel:\+?[0-9 ().-]{6,}$', unquote(h), re.I))
            return ok, ('Teléfono ' if ok else 'Teléfono no válido: ') + unquote(h[4:])[:40]
        u = urlparse(h)
        bad = re.search(r'undefined|null|\$\{|\s|…', h)
        if u.scheme == 'https' and u.hostname and '.' in u.hostname and not bad:
            return True, f'Enlace externo a {u.hostname} (no se abre: dirección https válida)'
        if u.scheme == 'http' and u.hostname and not bad:
            return False, f'Enlace externo sin https: {h[:100]}'
        return False, f'Dirección externa no válida: {h[:100]}'

    def check_same_origin_link(self, e, rec):
        url = e.get('abs') or (self.base + e['href'])
        url = re.sub(r'^http://(127\.0\.0\.1|localhost)(:\d+)?', self.base, url)
        if not url.startswith(self.base):
            ok, why = self.valid_external(url)
            rec['result'], rec['detail'] = ('Funciona' if ok else 'Error'), why
            return
        from e2e_markers import ADMIN_REASON
        try:
            r = self.ctx.request.get(url, headers={'x-admin-reason': ADMIN_REASON}, timeout=20000, max_redirects=0)
            st, ct = r.status, (r.headers.get('content-type') or '').split(';')[0]
            disp = r.headers.get('content-disposition') or ''
        except Exception as ex:
            rec['result'], rec['detail'] = 'Error', f'La dirección {url[len(self.base):]} no responde: {str(ex)[:100]}'
            return
        what = 'descarga' if (e.get('download') or 'attachment' in disp) else ('abre en otra pestaña' if e.get('target') == '_blank' else 'abre')
        path = url[len(self.base):][:100]
        if st >= 500:
            rec['result'], rec['detail'] = 'Error', f'{path} → {st} ({ct})'
        elif st >= 400:
            body = ''
            try:
                body = (r.json() or {}).get('error', '')
            except Exception:
                pass
            kk = [n for n, rx in KEY_RX if body and rx.search(body)]
            rec['result'] = 'Depende de clave pendiente' if kk else 'Error'
            rec['detail'] = f'Enlace roto: {path} → {st}' + (f' «{body[:120]}»' if body else '')
        else:
            rec['result'], rec['detail'] = 'Funciona', f'{what.capitalize()} {path} ({st}, {ct or "sin tipo"})'


# ------------------------------------------------------------------------------------------------ worker and report
def worker(role, demo, out, max_screens, part='todo'):
    logf = open(out.with_suffix('.log'), 'w', encoding='utf-8')
    t0 = time.time()

    def log(msg):
        print(msg, file=logf, flush=True)
    cr = RoleCrawler(role, Path(demo), max_screens, log, part)

    def dump(err):
        data = {'role': role, 'part': part, 'name': cr.role_name, 'screens': cr.screens, 'records': cr.records, 'error': err,
                'seconds': getattr(cr, 'seconds', None) or round(time.time() - t0), 'server_restarts': cr.server_restarts,
                'left_out': getattr(cr, 'left_out', [])}
        out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
    import signal

    def stop(*_):   # stopped from outside: keep what was done
        try:
            dump('Recorrido interrumpido desde fuera (SIGTERM)')
            cr.srv and cr.srv.stop()
        finally:
            os._exit(1)
    signal.signal(signal.SIGTERM, stop)
    err = None
    try:
        cr.run()
    except Exception:
        err = traceback.format_exc()
        log(err)
        try:
            cr.srv and cr.srv.stop()
        except Exception:
            pass
    dump(err)
    logf.close()


def merge_parts(ds):
    """One role from its parts (public first): screens renumbered; a screen opened by both parts is kept once."""
    out = {k: v for k, v in ds[0].items() if k not in ('screens', 'records')}
    out.update({'screens': [], 'records': [], 'seconds': max(d.get('seconds') or 0 for d in ds), 'parts': [d.get('part') for d in ds],
                'server_restarts': sum(d.get('server_restarts') or 0 for d in ds), 'left_out': sum((d.get('left_out') or [] for d in ds), []),
                'error': '\n'.join(d['error'] for d in ds if d.get('error')) or None})
    keys = set()
    for d in ds:
        remap = {}
        for s in d['screens']:
            if s.get('key') in keys:
                continue
            keys.add(s.get('key'))
            remap[s.get('id')] = len(out['screens'])
            out['screens'].append({**s, 'id': len(out['screens']), 'part': d.get('part')})
        for x in d['records']:
            if x['screen'] in remap:
                out['records'].append({**x, 'screen': remap[x['screen']]})
    return out


def md_cell(s):
    return str(s or '').replace('|', '\\|').replace('\n', ' ').strip()


def repro(role, screen, x):
    _, user, pw = ROLES[role]
    who = 'Sin iniciar sesión' if not user else (f'Entra como `{user}` (contraseña `{pw}`)' if role != 'admin' else 'Entra con una cuenta de administración')
    steps = [who, f"abre `{screen.get('route') or x['route']}`"]
    if screen.get('labels'):
        steps.append('pulsa la subpestaña «' + ' › '.join(screen['labels']) + '»')
    if screen.get('cookies'):
        steps.append('con el aviso de cookies sin aceptar')
    if x['tag'] == 'form':
        steps.append(f"vacía el formulario «{x['label']}» y envíalo")
    elif x['tag'] == 'select':
        steps.append(f"en «{x['label'][:40]}» elige otra opción")
    else:
        steps.append(f"pulsa «{x['label'][:60]}»")
    return '; '.join(steps) + '.'


def findings(parts, order):
    out = []
    for r in order:
        d = parts[r]
        scr = {s['id']: s for s in d['screens'] if 'id' in s}
        rows = []
        for s in d['screens']:
            for i in s.get('issues', []):
                rows.append({'screen': s['title'], 'route': s['route'], 'label': '(al abrir la pantalla)', 'kind': 'Pantalla', 'tag': 'screen',
                             'result': 'Error', 'detail': i, 'repro': repro(r, s, {'tag': 'screen', 'label': '', 'route': s['route']}).replace('; pulsa «».', '.')})
        for x in d['records']:
            if x['result'] in ('Error', 'Sin efecto') and not x.get('copied'):
                s = scr.get(x['screen'], {})
                rows.append({'screen': s.get('title', x['screen_title']), 'route': s.get('route', x['route']), 'label': x['label'], 'kind': x['kind'],
                             'tag': x['tag'], 'result': x['result'], 'detail': x['detail'] or 'No pasa nada visible y no se llama al servidor',
                             'repro': repro(r, s, x)})
        if rows:
            out.append((d['name'], rows))
    return out


def key_rows(parts, order):
    rows = []
    for r in order:
        d = parts[r]
        for x in d['records']:
            if x['result'] == 'Depende de clave pendiente' and not x.get('copied'):
                rows.append((d['name'], x['screen_title'], x['route'], x['label'], x['detail']))
        notices = {}
        for s in d['screens']:      # the same notice on many screens (the ArcGIS one of the administration) is listed once
            if (s.get('route') or '').startswith('#/legal'):
                continue            # legal texts name the providers (SMTP, Esri…): that is not a pending key
            for k in s.get('keys', []):
                notices.setdefault(k, []).append(s)
        for k, ss in notices.items():
            more = f' (y en {len(ss) - 1} pantallas más)' if len(ss) > 1 else ''
            rows.append((d['name'], ss[0]['title'] + more, ss[0]['route'], '(aviso en la pantalla)', k))
    return rows


def write_findings(parts, path: Path):
    order = [r for r in ROLES if r in parts]
    tot = {r: Counter(x['result'] for x in parts[r]['records']) for r in order}
    L = ['# Inventario de botones · hallazgos', '', 'Recuentos por papel:', '', '| Papel | ' + ' | '.join(STATUSES) + ' |', '|---|' + '---:|' * len(STATUSES)]
    for r in order:
        L.append(f"| {parts[r]['name']} | " + ' | '.join(str(tot[r].get(s, 0)) for s in STATUSES) + ' |')
    L += ['', '## «Error» y «Sin efecto»', '']
    for name, rows in findings(parts, order):
        L += [f'### {name}', '']
        for f in rows:
            L.append(f"- **{f['result']}** · {f['screen']} (`{f['route']}`) · {f['kind']} «{f['label']}»: {f['detail']}  \n  Reproducir: {f['repro']}")
        L.append('')
    L += ['## Depende de una clave pendiente', '']
    for n, scr, route, lab, det in key_rows(parts, order):
        L.append(f'- {n} · {scr} (`{route}`) · {lab}: {det}')
    path.write_text('\n'.join(L) + '\n', encoding='utf-8')


def write_report(parts, outdir: Path, meta: dict):
    outdir.mkdir(parents=True, exist_ok=True)
    order = [r for r in ROLES if r in parts]
    lines = ['# Inventario de botones, enlaces y formularios', '',
             f"Generado el {meta['date']} con `tests/navegador/inventario_botones.py` en Chromium (escritorio 1366×900, es-ES).",
             'Cada papel usa su propio servidor con una copia nueva de la base de demostración (`scripts/crear_demo.py`), sin claves '
             'externas (Stripe, WhatsApp/Meta, SMTP, ArcGIS, Firebase) y sin salida a internet.', '',
             '## Cómo se ha probado', '',
             '- Se abren todas las pantallas a las que llega cada papel: rutas públicas, páginas de la cuenta, cada pestaña del panel y cada '
             'subpestaña (se descubren siguiendo los enlaces internos y las pestañas).',
             '- En cada pantalla se enumeran los elementos visibles: `a[href]`, `button`, `[role=button]`, `input[type=submit|button]`, '
             '`select` y formularios. Cada uno se prueba aislado: se recarga la pantalla, se pulsa (un formulario se envía **vacío**; '
             'en un desplegable se elige otra opción), se cancela cualquier `confirm()`/`prompt()` y se observa durante ~1,5 s.',
             '- **Funciona**: efecto visible (navegación, ventana, aviso, validación, cambio de estado o de contenido, descarga) sin error de JavaScript ni 5xx.',
             '- **Depende de clave pendiente**: la respuesta o el aviso dicen que falta configurar un servicio (Stripe, WhatsApp, correo SMTP, '
             'ArcGIS/satélite, Firebase/push, Wikimedia).',
             '- **Sin efecto**: no pasa nada visible ni se llama al servidor; antes de darlo por bueno se repite en una pantalla recién abierta '
             'esperando 3,5 s. **Error**: error de JavaScript, respuesta 5xx, enlace roto, ruta inexistente o mensaje técnico a la vista.',
             '- **No probado**: el elemento ya no aparece al volver a abrir la pantalla (ni siquiera con una copia nueva de la base).',
             '- **Desactivado (correcto)**: desactivado con un texto que explica por qué; **Desactivado (sin explicación)**: sin ese texto.',
             '- Los enlaces externos no se abren: se comprueba que son direcciones `https` válidas (o `mailto:`/`tel:` bien formados). '
             'Los enlaces a archivos del propio servidor se piden y se comprueba la respuesta.',
             '- La cabecera, el pie y el menú lateral de los paneles se prueban una vez por papel (en la primera pantalla donde aparecen). '
             f'En listas de {GROUP_MIN} o más elementos iguales se prueban los {GROUP_TESTED} primeros (el primero si son enlaces); '
             'un enlace interno que ya se ha pulsado en otra pantalla del mismo papel se anota con el mismo resultado («Mismo enlace…»).',
             '- Con sesión, cada papel se recorre en dos partes a la vez (páginas públicas y páginas privadas: cuenta y panel), cada una '
             'con su servidor y su copia nueva de la base. Si una prueba cambia los datos y un elemento desaparece, se vuelve a una copia nueva.',
             '- «Cerrar sesión», «Borrar/Cerrar mi cuenta», «Restaurar demo» y parecidos se prueban al final del papel, solo hasta la confirmación (que se cancela).', '']
    # summary
    lines += ['## Resumen por papel', '', '| Papel | Pantallas | Pantallas con error al abrir | Elementos | ' + ' | '.join(STATUSES) + ' |',
              '|---|---:|---:|---:|' + '---:|' * len(STATUSES)]
    tot = Counter()
    for r in order:
        d = parts[r]
        c = Counter(x['result'] for x in d['records'])
        tot.update(c)
        tot['_screens'] += len(d['screens'])
        bad_screens = sum(1 for s in d['screens'] if s.get('issues'))
        tot['_bad'] += bad_screens
        lines.append(f"| {d['name']} | {len(d['screens'])} | {bad_screens} | {len(d['records'])} | " + ' | '.join(str(c.get(s, 0)) for s in STATUSES) + ' |')
    lines.append(f"| **Total** | {tot['_screens']} | {tot['_bad']} | {sum(tot[s] for s in STATUSES)} | " + ' | '.join(f'**{tot.get(s, 0)}**' for s in STATUSES) + ' |')
    lines.append('')
    for r in order:
        d = parts[r]
        if d.get('error'):
            lines += [f"> **Atención:** el recorrido de «{d['name']}» terminó con un fallo del propio inventario: `{md_cell(d['error'].strip().splitlines()[-1])}`", '']
        if d.get('left_out'):
            lines += [f"> «{d['name']}»: se alcanzó el máximo de pantallas; quedaron sin abrir: {', '.join('`' + x + '`' for x in d['left_out'][:20])}", '']
    # findings
    lines += ['## Hallazgos: «Error» y «Sin efecto»', '']
    found = findings(parts, order)
    if not found:
        lines += ['Ninguno.', '']
    for name, rows in found:
        lines += [f'### {name}', '', '| Pantalla | Elemento | Tipo | Resultado | Qué pasa | Cómo reproducirlo |', '|---|---|---|---|---|---|']
        for f in rows:
            lines.append(f"| {md_cell(f['screen'])} `{md_cell(f['route'])}` | {md_cell(f['label'])} | {md_cell(f['kind'])} | {f['result']} | {md_cell(f['detail'])} | {md_cell(f['repro'])} |")
        lines.append('')
    lines += ['## Depende de una clave pendiente', '']
    keyed = key_rows(parts, order)
    if keyed:
        lines += ['| Papel | Pantalla | Elemento | Detalle |', '|---|---|---|---|']
        for n, scr, route, lab, det in keyed:
            lines.append(f"| {md_cell(n)} | {md_cell(scr)} `{md_cell(route)}` | {md_cell(lab)} | {md_cell(det)} |")
    else:
        lines.append('Ninguno.')
    lines.append('')
    # full inventory
    lines += ['## Inventario completo', '']
    for r in order:
        d = parts[r]
        lines += [f"### {d['name']}", '']
        if d.get('seconds'):
            lines += [f"{len(d['screens'])} pantallas, {len(d['records'])} elementos probados en {d['seconds'] // 60} min {d['seconds'] % 60} s.", '']
        recs = d['records']
        common = [x for x in recs if x['zone'] in ('cabecera', 'pie', 'flotante', 'cookies')]
        if common:
            lines += ['#### Cabecera, pie y elementos flotantes (comunes a todas las pantallas)', '',
                      '| Pantalla | Elemento | Tipo | Resultado | Detalle |', '|---|---|---|---|---|']
            for x in common:
                lines.append(f"| {md_cell(x['screen_title'])} · {ZONE_NAMES.get(x['zone'], x['zone'])} | {md_cell(x['label'])} | {md_cell(x['kind'])} | {x['result']} | {md_cell(x['detail'])} |")
            lines.append('')
        for s in d['screens']:
            xs = [x for x in recs if x['screen'] == s.get('id') and x['zone'] not in ('cabecera', 'pie', 'flotante', 'cookies')]
            title = f"#### {md_cell(s['title'])} · `{md_cell(s['route'])}`" + (f" ({len(s['clicks'])} clic en subpestaña)" if s.get('clicks') else '')
            lines += [title, '']
            if s.get('redirect'):
                lines += [f"Redirige: `{s['redirect']}`.", '']
            if s.get('notes'):
                lines += ['Al abrirla, el servidor responde con error a: ' + ', '.join(f'`{md_cell(n)}`' for n in s['notes']) + ' (la pantalla se ve bien; revisar si sobran esas llamadas).', '']
            if not xs and not s.get('issues'):
                lines += ['Sin elementos nuevos que probar (los comunes ya se han probado en otra pantalla).' if s.get('elements') else 'Sin elementos.', '']
                continue
            lines += ['| Pantalla | Elemento | Tipo | Resultado | Detalle |', '|---|---|---|---|---|']
            for i in s.get('issues', []):
                lines.append(f"| {md_cell(s['title'])} | (al abrir la pantalla) | Pantalla | Error | {md_cell(i)} |")
            for x in xs:
                lines.append(f"| {md_cell(s['title'])} | {md_cell(x['label'])} | {md_cell(x['kind'])} | {x['result']} | {md_cell(x['detail'])} |")
            lines.append('')
    (outdir / 'botones.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    raw = {'generated': meta['date'], 'browser': 'Chromium (Playwright)', 'viewport': DESK, 'locale': 'es-ES', 'statuses': STATUSES,
           'roles': {r: parts[r] for r in order}}
    (outdir / 'botones.json').write_text(json.dumps(raw, ensure_ascii=False, indent=1), encoding='utf-8')
    return tot


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--demo', help='base de demostración ya creada (si no, se crea con scripts/crear_demo.py)')
    ap.add_argument('--roles', default=','.join(ROLES), help='papeles separados por comas: ' + ','.join(ROLES))
    ap.add_argument('--paralelo', type=int, default=3, help='papeles a la vez (cada uno con su servidor y su navegador)')
    ap.add_argument('--max-pantallas', type=int, default=150)
    ap.add_argument('--salida', default=str(ROOT / 'docs' / 'auditoria'))
    ap.add_argument('--trabajo', help='carpeta para los resultados parciales (por defecto, una temporal)')
    ap.add_argument('--hallazgos', help='escribe también la lista de «Error», «Sin efecto» y claves pendientes en este archivo .md')
    ap.add_argument('--solo-informe', action='store_true', help='no recorre nada: rehace el informe con los resultados de --trabajo')
    ap.add_argument('--partes', default='si', choices=['si', 'no'], help='con sesión, la parte pública y la privada en paralelo (dos servidores)')
    ap.add_argument('--parte', default='todo', help=argparse.SUPPRESS)
    ap.add_argument('--worker', help=argparse.SUPPRESS)
    ap.add_argument('--out', help=argparse.SUPPRESS)
    a = ap.parse_args()
    if a.worker:
        worker(a.worker, a.demo, Path(a.out), a.max_pantallas, a.parte)
        return
    work = Path(a.trabajo or tempfile.mkdtemp(prefix='wod-inventario-'))
    work.mkdir(parents=True, exist_ok=True)
    demo = Path(a.demo) if a.demo else None
    if not demo and not a.solo_informe:
        demo = work / 'demo.sqlite3'
        print('Creando la base de demostración…', flush=True)
        r = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'crear_demo.py'), '--out', str(demo)], capture_output=True, text=True)
        if r.returncode != 0 or not demo.exists():
            sys.exit('No se ha podido crear la base de demostración:\n' + r.stdout + r.stderr)
    roles = [r.strip() for r in a.roles.split(',') if r.strip()]
    for r in roles:
        if r not in ROLES:
            sys.exit(f'Papel desconocido: {r}')
    jobs = []
    for r in roles:   # the private parts (panels) first: they are the longest
        jobs += [(r, 'privada')] if ROLES[r][1] and a.partes == 'si' else []
    for r in roles:
        jobs += [(r, 'publica' if ROLES[r][1] and a.partes == 'si' else 'todo')]
    pending = [] if a.solo_informe else jobs
    running = {}
    t0 = time.time()
    while pending or running:
        while pending and len(running) < max(1, a.paralelo):
            r, part = pending.pop(0)
            out = work / f'{r}-{part}.json'
            running[(r, part)] = (subprocess.Popen([sys.executable, __file__, '--worker', r, '--parte', part, '--demo', str(demo), '--out', str(out),
                                                    '--max-pantallas', str(a.max_pantallas)]), out)
            print(f'[{time.time() - t0:6.0f} s] empieza {r} ({part}) · registro: {out.with_suffix(".log")}', flush=True)
        time.sleep(2)
        for k, (pr, out) in list(running.items()):
            if pr.poll() is not None:
                print(f'[{time.time() - t0:6.0f} s] termina {k[0]} ({k[1]}) · código {pr.returncode}', flush=True)
                del running[k]
    parts = {}
    for r in roles:
        files = sorted(work.glob(f'{r}-*.json'), key=lambda f: ('publica' not in f.name and 'todo' not in f.name, f.name))
        if files:
            parts[r] = merge_parts([json.loads(f.read_text(encoding='utf-8')) for f in files])
    # keep the other roles of a previous run when only some are repeated
    prev = Path(a.salida) / 'botones.json'
    if prev.exists() and set(roles) != set(ROLES):
        try:
            old = json.loads(prev.read_text(encoding='utf-8')).get('roles', {})
            for r, d in old.items():
                parts.setdefault(r, d)
        except Exception:
            pass
    tot = write_report(parts, Path(a.salida), {'date': dt.datetime.now().strftime('%d/%m/%Y %H:%M')})
    if a.hallazgos:
        write_findings(parts, Path(a.hallazgos))
    print('\n'.join(f'{s}: {tot.get(s, 0)}' for s in STATUSES))
    print(f'Informe: {Path(a.salida) / "botones.md"} · {time.time() - t0:.0f} s')


if __name__ == '__main__':
    main()
