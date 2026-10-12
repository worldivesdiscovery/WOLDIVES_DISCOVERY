"""v50.46 · Cambios del 12/10/2026, puntos 2 y 3 (browser, Playwright).

Legal pages (one template for all of them):
- no legal page scrolls sideways, no element goes out of the screen and no block is painted over another, at 360,
  390, 768, 1024 and 1440 px, with the default theme and with a second theme, in Spanish (every page) and in the
  other 8 languages (the pages with tables and the reference page);
- the «Contacto» form sends: visible labels, button, message with the reference;
- on phones the tables become cards (each cell shows its column name).
Logo once per screen:
- the symbol (globe and diver) appears at most once on every screen checked, and the header keeps its logo.

    python tests/e2e_legal_logo.py
"""
from __future__ import annotations

import datetime
import json
import sys
import urllib.request
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1])]   # tests/navegador and tests (helpers)
from helpers import Server  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

CHROME = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
LANGS = ['es', 'en', 'fr', 'de', 'it', 'pt', 'nl', 'pl', 'zh']
WIDTHS = [360, 390, 768, 1024, 1440]
MEASURE = """()=>{const out={scroll:document.documentElement.scrollWidth>innerWidth+1,wide:[],overlap:[]};
 for(const e of document.querySelectorAll('.lg-page *')){const r=e.getBoundingClientRect(); if(r.width>0&&r.height>0&&r.right>innerWidth+1&&!e.closest('thead')) out.wide.push(e.tagName+'.'+e.className);}
 const blocks=[...document.querySelectorAll('.lg-doc > *, .lg-main > *, .lg-side > *, .lg-nav, .lg-hero')].filter(e=>e.getBoundingClientRect().height>0);
 for(let i=0;i<blocks.length;i++)for(let j=i+1;j<blocks.length;j++){const a=blocks[i].getBoundingClientRect(),b=blocks[j].getBoundingClientRect();
  const ix=Math.min(a.right,b.right)-Math.max(a.left,b.left), iy=Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top);
  if(ix>4&&iy>4&&!blocks[i].contains(blocks[j])&&!blocks[j].contains(blocks[i])) out.overlap.push(blocks[i].className+' / '+blocks[j].className);}
 out.wide=out.wide.slice(0,3); out.overlap=out.overlap.slice(0,3); return out;}"""
SYMBOL_IMAGES = """()=>[...document.querySelectorAll('img')].filter(i=>{const r=i.getBoundingClientRect(); const s=getComputedStyle(i);
  return r.width>0&&r.height>0&&s.visibility!=='hidden'&&/\\/img\\/marca\\/(worldives-logo-(vertical|horizontal)|worldives-simbolo|worldives-icono)/.test(i.src);}).map(i=>i.src.split('/').pop())"""

results = []


def check(name, ok, detail=''):
    results.append((name, bool(ok)))
    print(('OK   ' if ok else 'FALLA') + ' ' + name + ('' if ok else f'  → {detail}'))


def main():
    srv = Server().start(); srv.stop(cleanup=False)
    now = datetime.datetime.now().isoformat()
    srv.sql("INSERT INTO site_themes(name,accent,mode,scope,created_at,updated_at) VALUES('Segundo tema','coral','off','all',?,?)", (now, now))
    srv.start()
    slugs = list(json.loads(urllib.request.urlopen(srv.base + '/api/legal/info').read())['docs'])

    def theme(on):
        srv.stop(cleanup=False); srv.sql("UPDATE site_themes SET mode=? WHERE name='Segundo tema'", ('always' if on else 'off',)); srv.start()
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(executable_path=CHROME)

            def page(width, lang='es'):
                ctx = b.new_context(viewport={'width': width, 'height': 860}, locale='es-ES')
                ctx.add_init_script("try{localStorage.setItem('wd_cookie_notice',String(Date.now()))}catch(e){}")
                pg = ctx.new_page(); errors = []
                pg.on('pageerror', lambda e: errors.append(str(e)))
                pg.goto(srv.base + f'/?lang={lang}#/'); pg.wait_for_timeout(700)
                return ctx, pg, errors

            def legal_ok(pg, label):
                bad = []
                for s in slugs:
                    pg.evaluate(f"location.hash='#/legal/{s}'"); pg.wait_for_timeout(450)
                    m = pg.evaluate(MEASURE)
                    if m['scroll'] or m['wide'] or m['overlap']: bad.append((s, m))
                check(f'legal · {label}: sin desplazamiento lateral ni solapes', not bad, bad[:2])

            for with_theme in (False, True):
                theme(with_theme)
                tname = 'segundo tema' if with_theme else 'tema por defecto'
                for w in WIDTHS:
                    ctx, pg, errors = page(w)
                    legal_ok(pg, f'es · {w}px · {tname}')
                    check(f'legal · es · {w}px · {tname}: sin errores JS', not errors, errors[:2])
                    ctx.close()
            theme(False)
            for lang in LANGS[1:]:
                for w in (390, 1440):
                    ctx, pg, errors = page(w, lang)
                    bad = []
                    for s in ('cookies', 'contacto', 'privacidad', 'aviso-legal'):
                        pg.evaluate(f"location.hash='#/legal/{s}'"); pg.wait_for_timeout(500)
                        m = pg.evaluate(MEASURE)
                        if m['scroll'] or m['wide'] or m['overlap']: bad.append((s, m))
                    check(f'legal · {lang} · {w}px: sin desplazamiento lateral ni solapes', not bad, bad[:2])
                    ctx.close()

            # tables become cards on phones
            ctx, pg, _ = page(390)
            pg.evaluate("location.hash='#/legal/cookies'"); pg.wait_for_timeout(700)
            disp = pg.evaluate("getComputedStyle(document.querySelector('.lg-table tr')).display")
            label = pg.evaluate("getComputedStyle(document.querySelector('.lg-table td'),'::before').content")
            check('móvil: cada fila de la tabla es una tarjeta con el nombre de la columna', disp == 'block' and label not in ('none', 'normal', '""'), (disp, label))
            # contact form
            pg.evaluate("location.hash='#/legal/contacto'"); pg.wait_for_timeout(900)
            check('contacto: enlace visible a «Denunciar contenido»', pg.locator('#contact-form a[href="#/legal/denuncias"]').is_visible())
            labels = [pg.locator(f'label[for="{i}"]').is_visible() for i in ('ct-topic', 'ct-name', 'ct-email', 'ct-msg')]
            check('contacto: etiquetas visibles', all(labels), labels)
            pg.select_option('#ct-topic', 'booking'); pg.wait_for_timeout(150)
            check('contacto: con «reserva» aparece el número de reserva', pg.locator('#ct-ref').is_visible())
            pg.fill('#ct-ref', 'WOD-00042'); pg.fill('#ct-name', 'Ana Pérez'); pg.fill('#ct-email', 'ana@buceo-ana.es')
            pg.fill('#ct-msg', 'Quiero cambiar la hora de mi reserva del sábado.'); pg.check('#ct-privacy')
            pg.click('#contact-form button[type=submit]'); pg.wait_for_timeout(900)
            txt = pg.inner_text('#lg-contact')
            check('contacto: el formulario envía y muestra la referencia', 'Mensaje enviado' in txt and 'CON-' in txt, txt[:120])
            check('contacto: el mensaje llega a la base', bool(srv.sql("SELECT 1 FROM contact_messages WHERE booking_ref='WOD-00042'")))
            pg.screenshot(path=str(Path(__file__).resolve().parents[2] / 'docs' / 'capturas' / 'cambios-12-10-v50-46' / 'despues' / 'contacto-enviado-movil.png'))
            ctx.close()

            # logo once per screen
            for w in (1366, 390):
                ctx, pg, _ = page(w)
                for route in ('#/', '#/login', '#/registro', '#/recuperar', '#/explorar', '#/centros', '#/experiencias', '#/legal/contacto', '#/setup'):
                    pg.evaluate(f"location.hash='{route}'"); pg.wait_for_timeout(800)
                    imgs = pg.evaluate(SYMBOL_IMAGES)
                    check(f'logo · {w}px · {route}: el símbolo aparece una vez como mucho', len(imgs) <= 1, imgs)
                header = pg.locator('.site-header .brand img')
                check(f'logo · {w}px: la cabecera mantiene su logo', header.count() == 1 and header.first.is_visible())
                ctx.close()
            b.close()
    finally:
        srv.stop()
    ok = sum(1 for _, x in results if x)
    print(f'{ok}/{len(results)} comprobaciones correctas')
    sys.exit(0 if ok == len(results) else 1)


if __name__ == '__main__':
    main()
