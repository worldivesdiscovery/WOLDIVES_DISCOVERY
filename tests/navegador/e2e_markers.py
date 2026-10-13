"""Fase 1C: screenshots of the map markers before (v50.30) and after, desktop and phone, base map and satellite,
and a smoothness check with every dive site on a phone. Tile servers are simulated (no internet in CI):
a light «map» tile and a dark «satellite» tile, enough to judge contrast and size.

Usage: python tests/e2e_markers.py SHOTS_DIR [--before-root PATH_TO_V50_30_CHECKOUT]
"""
from __future__ import annotations

import os
import struct
import subprocess
import sys
import time
import zlib
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1])]   # tests/navegador and tests (helpers)
from helpers import Server, free_port  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402


def png(w, h, fn):
    rows = b''.join(b'\x00' + b''.join(bytes(fn(x, y)) for x in range(w)) for y in range(h))
    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(rows, 6)) + chunk(b'IEND', b'')


MAP_TILE = png(256, 256, lambda x, y: (170, 211, 223) if (x * 7 + y * 3) % 211 > 60 else (242, 239, 233))
SAT_TILE = png(256, 256, lambda x, y: (20 + (x * y) % 30, 45 + (x + y) % 40, 60 + (x * 3) % 50))


# v50.47 (B.9): an administrator gives a reason before seeing a centre's data (header X-Admin-Reason; the web asks for
# it with prompt()). In the automatic walks every request carries the reason, so the administration pages open as they
# do for a person who wrote it; for anybody else the header is ignored by the server.
ADMIN_REASON = 'Revision de las pruebas automaticas'


def _with_reason(ctx):
    ctx.route('**/api/**', lambda r: r.continue_(headers={**r.request.headers, 'x-admin-reason': ADMIN_REASON}))
    return ctx


def chromium(p):
    exe = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
    b = p.chromium.launch(executable_path=exe) if Path(exe).exists() else p.chromium.launch()
    new_context = b.new_context
    b.new_context = lambda *a, **k: _with_reason(new_context(*a, **k))
    b.new_page = lambda *a, **k: b.new_context(*a, **k).new_page()
    return b


def shoot(base, shots: Path, tag: str, results: list):
    with sync_playwright() as p:
        b = chromium(p)
        for dev, opts in (('ordenador', {'viewport': {'width': 1366, 'height': 900}}),
                          ('movil', {'viewport': {'width': 390, 'height': 844}, 'is_mobile': True, 'has_touch': True, 'device_scale_factor': 2})):
            ctx = b.new_context(**opts)
            page = ctx.new_page()
            page.route('**/*tile.openstreetmap.org/**', lambda r: r.fulfill(body=MAP_TILE, content_type='image/png'))
            page.route('**/server.arcgisonline.com/**', lambda r: r.fulfill(body=SAT_TILE, content_type='image/png'))
            page.route('**/wms.gebco.net/**', lambda r: r.fulfill(body=MAP_TILE, content_type='image/png'))
            vend = Path(__file__).resolve().parents[2] / 'public' / 'lib' / 'leaflet'
            def unpkg(r):  # v50.30 loaded Leaflet from unpkg (blocked here): serve the same 1.9.4 files locally
                name = r.request.url.split('/dist/')[-1]
                f = vend / name
                r.fulfill(body=f.read_bytes(), content_type='text/css' if name.endswith('.css') else ('image/png' if name.endswith('.png') else 'application/javascript')) if f.exists() else r.abort()
            page.route('**/unpkg.com/**', unpkg)
            page.goto(base + '/#/explorar')
            page.wait_for_load_state('networkidle'); page.wait_for_timeout(1500)
            try:
                page.evaluate("document.querySelector('.cookie-notice button, .ck-ok, #cookie-ok')?.click()")
            except Exception:
                pass
            page.locator('.map-card, #explore-map').first.scroll_into_view_if_needed()
            page.wait_for_timeout(600)
            # Zoom to the Spanish Mediterranean coast where many points are close together.
            page.evaluate("""()=>{ try{ const m=document.querySelector('#explore-map')._leaflet_id; }catch(e){} }""")
            for mode, label in (('street', 'mapa'), ('satellite', 'satelite')):
                btn = page.locator(f'.map-toolbar button[data-mapmode="{mode}"]')
                if btn.count() and btn.first.is_visible() and btn.first.is_enabled():
                    btn.first.click(); page.wait_for_timeout(700)
                elif mode == 'satellite':
                    continue   # satellite needs ARCGIS_API_KEY (Fase 5.10); without it the button is disabled (v50.43)
                el = page.locator('#explore-map')
                el.screenshot(path=str(shots / f'{tag}-{dev}-{label}-mundo.png'))
                page.evaluate("()=>{ const L_=window.L; }")
                # zoom in with the + control three times around the visible markers
                for _ in range(3):
                    page.locator('.leaflet-control-zoom-in').first.click(); page.wait_for_timeout(900)
                el.screenshot(path=str(shots / f'{tag}-{dev}-{label}-zoom.png'))
                for _ in range(3):
                    page.locator('.leaflet-control-zoom-out').first.click(); page.wait_for_timeout(300)
            # marker size actually drawn
            size = page.evaluate("""()=>{ const e=document.querySelector('#explore-map .wd-pin')||document.querySelector('#explore-map .leaflet-marker-icon'); if(!e) return null; const r=e.getBoundingClientRect(); const w=e.closest('.leaflet-marker-icon')||e; const rw=w.getBoundingClientRect(); return [Math.round(r.width),Math.round(r.height),Math.round(rw.width),Math.round(rw.height)]; }""")
            results.append((tag, dev, 'tamaño dibujo/zona táctil (px)', size))
            if tag == 'despues' and dev == 'movil':
                ctx.new_cdp_session(page).send('Emulation.setCPUThrottlingRate', {'rate': 4})
                # Smoothness: animate 60 pans with every dive site loaded and count frames over 50 ms.
                fps = page.evaluate("""async()=>{ const map=Object.values(window).find(v=>v&&v._leaflet_id&&v.panBy)||null; return null; }""")
                stats = page.evaluate("""async()=>{ const el=document.querySelector('#explore-map'); const r=el.getBoundingClientRect(); const frames=[]; let last=performance.now(), run=true;
                    const tick=t=>{ frames.push(t-last); last=t; if(run) requestAnimationFrame(tick); }; requestAnimationFrame(tick);
                    const start=performance.now(); const ev=(type,x,y)=>el.dispatchEvent(new PointerEvent(type,{clientX:x,clientY:y,bubbles:true,pointerType:'mouse',isPrimary:true,buttons:1}));
                    let x=r.left+r.width/2, y=r.top+r.height/2; const md=(t,xx,yy)=>el.dispatchEvent(new MouseEvent(t,{clientX:xx,clientY:yy,bubbles:true,buttons:1}));
                    md('mousedown',x,y); for(let i=0;i<60;i++){ x+= (i<30?6:-6); y+= (i%2?2:-2); md('mousemove',x,y); await new Promise(res=>requestAnimationFrame(res)); } md('mouseup',x,y);
                    run=false; const total=performance.now()-start; const slow=frames.filter(f=>f>50).length; return {frames:frames.length,total_ms:Math.round(total),slow_frames:slow,avg_ms:Math.round(frames.reduce((a,b)=>a+b,0)/frames.length)}; }""")
                markers = page.evaluate("document.querySelectorAll('.wd-pin,.wd-cluster').length")
                results.append((tag, dev, 'fluidez al mover el mapa (CPU x4 en móvil emulado)', stats))
                results.append((tag, dev, 'elementos dibujados (marcadores + grupos)', markers))
            ctx.close()
        b.close()


def main():
    shots = Path(sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else Path(__file__).resolve().parents[2] / 'docs' / 'capturas' / 'fase-1c'); shots.mkdir(parents=True, exist_ok=True)
    results = []
    # AFTER (this version)
    s = Server().start()
    try:
        shoot(s.base, shots, 'despues', results)
    finally:
        s.stop()
    # BEFORE (v50.30 checkout), when given
    if '--before-root' in sys.argv:
        root = Path(sys.argv[sys.argv.index('--before-root') + 1])
        port = free_port()
        env = dict(os.environ, WOD_PORT=str(port))
        proc = subprocess.Popen([sys.executable, str(root / 'app' / 'server.py')], cwd=str(root), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            import urllib.request
            for _ in range(100):
                try:
                    urllib.request.urlopen(f'http://127.0.0.1:{port}/api/health', timeout=1); break
                except Exception:
                    time.sleep(0.1)
            shoot(f'http://127.0.0.1:{port}', shots, 'antes', results)
        finally:
            proc.terminate()
    for r in results:
        print(*r)


if __name__ == '__main__':
    main()
