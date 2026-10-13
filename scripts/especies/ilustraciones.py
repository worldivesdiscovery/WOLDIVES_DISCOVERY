#!/usr/bin/env python3
"""Own illustrations of the example species (v50.50), drawn here as SVG and rendered to WebP with the browser.

They are WORLDIVES DISCOVERY's own work (licence «Ilustración propia»), made because the example catalogue cannot use
photos from the internet without a licence. On the real server the administrator can replace each one by a free photo
of Wikimedia Commons (Administración → Vida marina y vídeos → Especies → Editar → «Buscar una foto libre…»).

    python scripts/especies/ilustraciones.py            → public/img/especies/<clave>-320|640|1280.webp (4:3)
    python scripts/especies/ilustraciones.py --svg DIR  → also keeps the SVG files in DIR
"""
from __future__ import annotations

import io
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'public' / 'img' / 'especies'
WIDTHS = (320, 640, 1280)   # the same sizes as an uploaded species photo (wod.vidamarina.SPECIES_WIDTHS)
W, H = 800, 600


# --- scene -------------------------------------------------------------------------------------------------------------
def scene(key, body, tropical=False, seed=1, floor='rocks'):
    rnd = random.Random(seed)
    top, mid, deep = (('#3fb7c9', '#137a99', '#073d5a') if tropical else ('#3a8fb5', '#11587c', '#062b45'))
    rays = ''.join(f'<polygon points="{x},0 {x + w},0 {x + w * 2.6 + 120},600 {x + 40},600" fill="#e8fbff" opacity="{op}"/>'
                   for x, w, op in ((rnd.randint(40, 200), 40, .07), (rnd.randint(300, 420), 60, .06), (rnd.randint(520, 660), 34, .07)))
    bubbles = ''.join(f'<circle cx="{rnd.randint(30, 770)}" cy="{rnd.randint(20, 420)}" r="{rnd.choice((2, 3, 3, 4, 6))}" fill="none" stroke="#e8fbff" stroke-width="1.4" opacity=".45"/>'
                      for _ in range(14))
    motes = ''.join(f'<circle cx="{rnd.randint(0, 800)}" cy="{rnd.randint(0, 600)}" r="1.2" fill="#e8fbff" opacity=".25"/>' for _ in range(60))
    if floor == 'rocks':
        ground = ('<path d="M0 500 C90 470 160 488 240 478 C330 466 400 494 480 486 C580 476 650 456 800 474 L800 600 L0 600 Z" fill="#0b2f40"/>'
                  '<path d="M0 540 C120 520 220 534 330 528 C450 520 560 540 800 520 L800 600 L0 600 Z" fill="#c9b48a" opacity=".55"/>'
                  + ''.join(f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="#123f52"/>' for x, y, rx, ry in ((70, 520, 90, 46), (690, 514, 120, 58), (420, 548, 70, 26)))
                  + ''.join(f'<path d="M{x} 560 C{x - 8} {520 - h // 3} {x + 10} {500 - h // 2} {x + rnd.randint(-14, 14)} {540 - h}" stroke="#3f7f5a" stroke-width="5" fill="none" stroke-linecap="round" opacity=".85"/>'
                            for x, h in ((200, 90), (214, 110), (226, 80), (560, 100), (574, 70), (590, 120), (330, 60))))
    elif floor == 'reef':
        corals = []
        for x in (40, 150, 610, 720):
            for i in range(5):
                a = -math.pi / 2 + (i - 2) * .35
                corals.append(f'<path d="M{x} 600 Q{x + math.cos(a) * 40} {560 + math.sin(a) * 40} {x + math.cos(a) * 70} {540 + math.sin(a) * 90}" stroke="{rnd.choice(("#e9775f", "#f2a65a", "#c95d8a", "#e8c46a"))}" stroke-width="{rnd.randint(9, 14)}" fill="none" stroke-linecap="round"/>')
        ground = ('<path d="M0 520 C120 500 260 520 400 510 C540 500 660 520 800 505 L800 600 L0 600 Z" fill="#e4d3a8" opacity=".75"/>' + ''.join(corals)
                  + '<ellipse cx="300" cy="575" rx="110" ry="28" fill="#5b8f7a" opacity=".8"/><ellipse cx="520" cy="585" rx="80" ry="22" fill="#7a5f9e" opacity=".75"/>')
    elif floor == 'sand':
        ground = ('<path d="M0 520 C150 505 300 525 460 515 C600 506 700 522 800 512 L800 600 L0 600 Z" fill="#d9c79c" opacity=".8"/>'
                  + ''.join(f'<path d="M{x} 560 q12 -6 24 0" stroke="#b9a476" stroke-width="2" fill="none"/>' for x in range(30, 800, 70)))
    else:
        ground = ''
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
            f'<defs><linearGradient id="sea" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{top}"/><stop offset=".55" stop-color="{mid}"/><stop offset="1" stop-color="{deep}"/></linearGradient>'
            '<radialGradient id="glow" cx=".45" cy="-.15" r=".95"><stop offset="0" stop-color="#d8f6ff" stop-opacity=".55"/><stop offset="1" stop-color="#d8f6ff" stop-opacity="0"/></radialGradient>'
            '<filter id="soft" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="6"/></filter></defs>'
            f'<rect width="{W}" height="{H}" fill="url(#sea)"/><rect width="{W}" height="{H}" fill="url(#glow)"/>{rays}{motes}{ground}{body}{bubbles}</svg>')


def grad(id_, a, b, vertical=True):
    xy = 'x1="0" y1="0" x2="0" y2="1"' if vertical else 'x1="0" y1="0" x2="1" y2="0"'
    return f'<linearGradient id="{id_}" {xy}><stop offset="0" stop-color="{a}"/><stop offset="1" stop-color="{b}"/></linearGradient>'


def eye(x, y, r, iris='#1b1b1b', ring='#f4e9c8'):
    return (f'<circle cx="{x}" cy="{y}" r="{r}" fill="{ring}"/><circle cx="{x}" cy="{y}" r="{r * .68}" fill="{iris}"/>'
            f'<circle cx="{x - r * .28}" cy="{y - r * .3}" r="{r * .22}" fill="#fff" opacity=".9"/>')


def shadow(cx, cy, rx, ry):
    return f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="#021622" opacity=".28" filter="url(#soft)"/>'


def fish(uid, cx, cy, L, Hh, top, belly, fin, tail='forked', dorsal='soft', pattern='', face=1.0, lips=False, extra=''):
    """A fish facing left. L: length without tail, Hh: height."""
    nx, tb = cx - L / 2, cx + L / 2
    body = (f'M{nx} {cy} C{nx + L * .12} {cy - Hh * .58} {cx + L * .18} {cy - Hh * .56} {tb} {cy - Hh * .13} '
            f'L{tb} {cy + Hh * .13} C{cx + L * .18} {cy + Hh * .56} {nx + L * .12} {cy + Hh * .6} {nx} {cy} Z')
    if tail == 'forked':
        t = f'M{tb - 6} {cy - Hh * .1} C{tb + L * .1} {cy - Hh * .2} {tb + L * .2} {cy - Hh * .55} {tb + L * .26} {cy - Hh * .6} C{tb + L * .17} {cy - Hh * .2} {tb + L * .17} {cy + Hh * .2} {tb + L * .26} {cy + Hh * .6} C{tb + L * .2} {cy + Hh * .55} {tb + L * .1} {cy + Hh * .2} {tb - 6} {cy + Hh * .1} Z'
    elif tail == 'round':
        t = f'M{tb - 8} {cy - Hh * .12} C{tb + L * .1} {cy - Hh * .5} {tb + L * .26} {cy - Hh * .42} {tb + L * .26} {cy} C{tb + L * .26} {cy + Hh * .42} {tb + L * .1} {cy + Hh * .5} {tb - 8} {cy + Hh * .12} Z'
    else:   # lunate (sharks, wrasse)
        t = f'M{tb - 8} {cy - Hh * .1} L{tb + L * .2} {cy - Hh * .62} C{tb + L * .14} {cy - Hh * .2} {tb + L * .14} {cy + Hh * .2} {tb + L * .2} {cy + Hh * .5} L{tb - 8} {cy + Hh * .1} Z'
    if dorsal == 'spiny':
        d = f'M{nx + L * .3} {cy - Hh * .47} ' + ''.join(f'L{nx + L * (.32 + i * .05)} {cy - Hh * (.72 if i % 2 == 0 else .5)} ' for i in range(10)) + f'L{tb - L * .05} {cy - Hh * .25} Z'
    elif dorsal == 'long':
        d = f'M{nx + L * .28} {cy - Hh * .46} C{nx + L * .45} {cy - Hh * .8} {tb - L * .12} {cy - Hh * .62} {tb - L * .02} {cy - Hh * .22} Z'
    else:
        d = f'M{nx + L * .38} {cy - Hh * .48} C{nx + L * .5} {cy - Hh * .85} {nx + L * .66} {cy - Hh * .7} {nx + L * .72} {cy - Hh * .4} Z'
    anal = f'M{cx + L * .05} {cy + Hh * .44} C{cx + L * .16} {cy + Hh * .7} {cx + L * .3} {cy + Hh * .55} {cx + L * .34} {cy + Hh * .3} Z'
    pect = f'M{nx + L * .3} {cy + Hh * .05} C{nx + L * .42} {cy + Hh * .05} {nx + L * .5} {cy + Hh * .28} {nx + L * .44} {cy + Hh * .36} C{nx + L * .38} {cy + Hh * .3} {nx + L * .32} {cy + Hh * .18} {nx + L * .3} {cy + Hh * .05} Z'
    ex, ey, er = nx + L * .14 * face, cy - Hh * .14, Hh * .085
    mouth = (f'<path d="M{nx + 2} {cy + Hh * .02} q{L * .05} {Hh * .07} {L * .08} {Hh * .03}" stroke="#2a1a12" stroke-width="{3 if lips else 2}" fill="none" stroke-linecap="round"/>')
    gill = f'<path d="M{nx + L * .26} {cy - Hh * .3} C{nx + L * .3} {cy - Hh * .05} {nx + L * .3} {cy + Hh * .15} {nx + L * .24} {cy + Hh * .35}" stroke="#00000033" stroke-width="3" fill="none"/>'
    return (f'<defs>{grad(uid + "b", top, belly)}<clipPath id="{uid}c"><path d="{body}"/></clipPath></defs>'
            + shadow(cx + 20, cy + Hh * .9, L * .45, Hh * .12)
            + f'<path d="{t}" fill="{fin}"/><path d="{d}" fill="{fin}"/><path d="{anal}" fill="{fin}"/>'
            + f'<path d="{body}" fill="url(#{uid}b)"/><g clip-path="url(#{uid}c)">{pattern}</g>'
            + f'<path d="{body}" fill="none" stroke="#00000030" stroke-width="2"/>{gill}<path d="{pect}" fill="{fin}" opacity=".9"/>{mouth}{eye(ex, ey, er)}{extra}')


def spots(rnd, x0, x1, y0, y1, n, r0, r1, color, op=.8):
    return ''.join(f'<ellipse cx="{rnd.uniform(x0, x1):.0f}" cy="{rnd.uniform(y0, y1):.0f}" rx="{rnd.uniform(r0, r1):.1f}" ry="{rnd.uniform(r0, r1) * .8:.1f}" fill="{color}" opacity="{op}"/>' for _ in range(n))


# --- species -----------------------------------------------------------------------------------------------------------
def mero():
    rnd = random.Random(3)
    pat = spots(rnd, 160, 640, 200, 420, 34, 8, 22, '#e8d9b0', .55)
    return scene('mero', fish('m', 390, 300, 440, 220, '#6b4a2f', '#a07b52', '#5a3d27', tail='round', dorsal='spiny', pattern=pat, lips=True), floor='rocks', seed=3)


def pulpo():
    rnd = random.Random(5)
    arms = []
    for i in range(8):
        a0 = math.radians(200 + i * 20)
        x0, y0 = 400 + math.cos(a0) * 40, 330
        pts = []
        for k in range(1, 5):
            r = 60 * k
            ang = a0 + math.sin(k * 1.1 + i) * .5
            pts.append((400 + math.cos(ang) * r * 1.3, 330 + abs(math.sin(ang)) * r * .55 + k * 30))
        d = f'M{x0:.0f} {y0} ' + ' '.join(f'Q{(pts[j][0] + (pts[j - 1][0] if j else x0)) / 2:.0f} {(pts[j][1] + (pts[j - 1][1] if j else y0)) / 2 + 20:.0f} {pts[j][0]:.0f} {pts[j][1]:.0f}' for j in range(4))
        arms.append(f'<path d="{d}" stroke="url(#pa)" stroke-width="{26 - i % 3 * 3}" fill="none" stroke-linecap="round"/>')
        arms.append(f'<path d="{d}" stroke="#f3c7a8" stroke-width="5" fill="none" stroke-dasharray="2 14" stroke-linecap="round" opacity=".8"/>')
    mantle = '<path d="M330 330 C300 230 330 140 410 130 C500 120 530 210 500 300 C485 345 360 360 330 330 Z" fill="url(#pm)"/>'
    mott = spots(rnd, 330, 500, 150, 320, 26, 4, 12, '#5b2416', .45)
    body = (f'<defs>{grad("pa", "#b2533a", "#d9825f")}{grad("pm", "#c66a48", "#8f3b26")}</defs>' + shadow(420, 545, 230, 22) + ''.join(arms) + mantle + mott
            + eye(372, 300, 13, '#2a1a10', '#f1d39a') + eye(452, 296, 13, '#2a1a10', '#f1d39a')
            + '<path d="M350 250 q30 -30 60 -6" stroke="#00000022" stroke-width="4" fill="none"/>')
    return scene('pulpo', body, floor='rocks', seed=5)


def morena():
    rnd = random.Random(7)
    rock = '<path d="M430 600 C440 470 520 380 640 360 C760 345 800 400 800 430 L800 600 Z" fill="#123f52"/><ellipse cx="560" cy="430" rx="70" ry="54" fill="#041a26"/>'
    path = 'M560 430 C500 400 460 330 400 300 C350 275 300 280 270 300'
    dots = ''.join(f'<circle cx="{rnd.randint(7, 53)}" cy="{rnd.randint(7, 53)}" r="{rnd.uniform(2.5, 5.5):.1f}" fill="#f0d27a" opacity=".85"/>' for _ in range(9))
    eel = (f'<defs>{grad("mo", "#4a3a22", "#6f5a35")}<pattern id="mop" width="60" height="60" patternUnits="userSpaceOnUse">{dots}</pattern></defs>'
           f'<path d="{path}" stroke="url(#mo)" stroke-width="64" fill="none" stroke-linecap="round"/>'
           f'<path d="{path}" stroke="url(#mop)" stroke-width="56" fill="none" stroke-linecap="round"/>')
    head = ('<path d="M300 268 C255 262 222 280 214 300 L262 300 C246 312 236 324 230 336 C262 338 292 330 310 318 Z" fill="#5a4629"/>'
            '<path d="M224 300 L258 300 L232 330 Z" fill="#7d2b25"/><path d="M226 300 l6 7 l6 -7 l6 7 l6 -7" stroke="#f6f0dc" stroke-width="2" fill="none"/>'
            + eye(262, 282, 7, '#111', '#d9c47a'))
    return scene('morena', rock + shadow(420, 520, 160, 18) + eel + head, floor='rocks', seed=7)


def caballito():
    grass = ''.join(f'<path d="M{x} 600 C{x - 10} 470 {x + 22} 330 {x + 6} {150 + i * 30}" stroke="#4d8a5a" stroke-width="{10 - i}" fill="none" stroke-linecap="round" opacity=".9"/>' for i, x in enumerate((470, 500, 540, 300, 260)))
    horse = ('M392 170 C372 160 340 168 330 186 C318 188 290 196 268 200 C264 208 268 214 276 214 C300 212 322 210 336 214 '
             'C344 236 352 250 360 262 C340 300 336 350 350 390 C362 430 392 452 420 452 C452 452 468 430 462 404 '
             'C456 380 434 372 420 384 C410 392 414 410 428 410 C440 410 442 398 436 394 '
             'C420 360 440 320 432 280 C428 250 420 224 412 206 C424 196 418 178 392 170 Z')
    body = (f'<defs>{grad("cb", "#c98a3c", "#e8b866")}</defs>' + grass + shadow(410, 540, 90, 14)
            + f'<path d="{horse}" fill="url(#cb)" stroke="#8a5a22" stroke-width="2"/>'
            + ''.join(f'<path d="M{x} {y} l{dx} -12" stroke="#8a5a22" stroke-width="3" stroke-linecap="round"/>' for x, y, dx in ((395, 175, 4), (408, 182, 8), (414, 224, 9), (424, 262, 10), (432, 300, 10), (430, 340, 10)))
            + ''.join(f'<circle cx="{x}" cy="{y}" r="2.6" fill="#fff6dd"/>' for x, y in ((372, 230), (388, 260), (380, 300), (400, 330), (392, 370), (410, 400), (368, 340), (356, 380)))
            + ''.join(f'<path d="M352 {y} h70" stroke="#00000022" stroke-width="2"/>' for y in range(280, 430, 18))
            + eye(352, 188, 7, '#1e140a', '#f2dcaa'))
    return scene('caballito', body, floor='sand', seed=9)


def sepia():
    rnd = random.Random(11)
    mantle = 'M260 300 C260 230 360 210 460 220 C560 230 600 270 600 300 C600 330 560 370 460 380 C360 390 260 370 260 300 Z'
    fin = 'M250 300 C250 210 370 196 470 206 C580 216 618 262 616 300 C618 338 580 384 470 394 C370 404 250 390 250 300 Z'
    stripes = ''.join(f'<path d="M{x} 225 q14 75 0 150" stroke="#f3ead8" stroke-width="7" fill="none" opacity=".7"/>' for x in range(300, 590, 34))
    arms = ''.join(f'<path d="M262 {y} C220 {y + d} 196 {y + d * 1.5} 170 {y + d * 2}" stroke="#a5795a" stroke-width="{11 - abs(d) // 6}" fill="none" stroke-linecap="round"/>' for y, d in ((286, -14), (296, -6), (304, 2), (312, 10), (318, 18)))
    body = (f'<defs>{grad("sp", "#8b6a50", "#c7a37d")}<clipPath id="spc"><path d="{mantle}"/></clipPath></defs>' + shadow(430, 500, 210, 20)
            + f'<path d="{fin}" fill="#e7d7bf" opacity=".85"/><path d="{mantle}" fill="url(#sp)"/><g clip-path="url(#spc)">{stripes}{spots(rnd, 300, 590, 230, 380, 30, 3, 9, "#5a3e2a", .4)}</g>'
            + arms + '<ellipse cx="282" cy="292" rx="20" ry="17" fill="#f2e6c9"/><path d="M270 292 q6 -8 12 0 q6 8 12 0" stroke="#1c140d" stroke-width="5" fill="none"/>')
    return scene('sepia', body, floor='sand', seed=11)


def pez_luna():
    disc = 'M210 300 C210 190 300 150 400 150 C500 150 560 200 580 260 C600 250 610 300 600 340 C580 400 500 450 400 450 C300 450 210 410 210 300 Z'
    body = (f'<defs>{grad("ml", "#8e9ea6", "#d7dde0")}</defs>' + shadow(410, 560, 190, 20)
            + '<path d="M470 168 C480 90 520 40 548 30 C552 80 540 140 520 200 Z" fill="#7d8c94"/><path d="M470 432 C480 510 520 560 548 570 C552 520 540 460 520 400 Z" fill="#7d8c94"/>'
            + f'<path d="{disc}" fill="url(#ml)" stroke="#6b7a82" stroke-width="2"/>'
            + '<path d="M575 262 C600 290 600 320 586 350" stroke="#6b7a82" stroke-width="10" fill="none" stroke-linecap="round"/>'
            + spots(random.Random(13), 260, 540, 190, 420, 22, 6, 16, '#ffffff', .25)
            + '<path d="M214 296 q8 6 16 0" stroke="#4a555b" stroke-width="3" fill="none"/>' + '<ellipse cx="300" cy="300" rx="18" ry="34" fill="#8e9ea6"/>' + eye(250, 270, 13, '#141a1e', '#e9eef0'))
    return scene('pez-luna', body, floor='none', seed=13)


def tortuga(key, shell1, shell2, skin, head_r, seed):
    rnd = random.Random(seed)
    shell = 'M260 300 C260 220 340 180 420 180 C520 180 580 230 590 300 C580 370 520 420 420 420 C330 420 260 380 260 300 Z'
    scutes = (''.join(f'<path d="M{x} {y} l34 -24 l40 0 l30 24 l-30 26 l-40 0 Z" fill="none" stroke="{shell2}" stroke-width="5" opacity=".85"/>' for x, y in ((330, 300), (400, 300), (470, 300)))
              + ''.join(f'<path d="M{x} {y} l30 -30 l38 6 l6 30" fill="none" stroke="{shell2}" stroke-width="4" opacity=".7"/>' for x, y in ((320, 250), (395, 240), (470, 250))))
    flip = lambda d: f'<path d="{d}" fill="{skin}" stroke="#00000033" stroke-width="2"/>'
    body = (f'<defs>{grad("ts" + key, shell1, shell2)}<clipPath id="tc{key}"><path d="{shell}"/></clipPath></defs>' + shadow(430, 540, 220, 20)
            + flip('M330 220 C300 150 230 110 170 120 C210 160 250 210 300 250 Z') + flip('M340 390 C320 450 270 490 220 490 C250 450 290 410 320 370 Z')
            + flip('M540 230 C580 200 620 196 640 206 C620 230 590 250 560 260 Z') + flip('M540 380 C580 410 610 420 630 414 C612 390 590 372 560 360 Z')
            + f'<path d="M262 300 C230 280 200 282 186 296 C178 312 196 330 226 330 C246 330 258 318 262 300 Z" fill="{skin}" transform="scale({head_r}) translate({(1 - head_r) * 220 / head_r:.0f} {(1 - head_r) * 306 / head_r:.0f})"/>'
            + f'<path d="{shell}" fill="url(#ts{key})" stroke="#00000044" stroke-width="3"/><g clip-path="url(#tc{key})">{scutes}{spots(rnd, 280, 580, 200, 400, 18, 4, 10, "#00000022", .5)}</g>'
            + eye(206 + (1 - head_r) * 30, 300, 6, '#111', '#e8dcc0'))
    return scene(key, body, tropical=key == 'tortuga-verde', floor='reef' if key == 'tortuga-verde' else 'sand', seed=seed)


def espeton():
    out = [f'<defs>{grad("es1", "#4f6f80", "#dfe8ec")}</defs>']
    for i, (cx, cy, L) in enumerate(((330, 260, 330), (520, 360, 260), (210, 400, 220), (600, 190, 200), (420, 470, 180))):
        Hh = L * .18
        nx, tb = cx - L / 2, cx + L / 2
        body = f'M{nx} {cy} L{nx + L * .12} {cy - Hh * .4} C{cx} {cy - Hh * .6} {tb - L * .1} {cy - Hh * .4} {tb} {cy - Hh * .14} L{tb} {cy + Hh * .14} C{tb - L * .1} {cy + Hh * .45} {cx} {cy + Hh * .55} {nx + L * .12} {cy + Hh * .3} Z'
        tail = f'M{tb - 4} {cy} L{tb + L * .14} {cy - Hh * .9} L{tb + L * .09} {cy} L{tb + L * .14} {cy + Hh * .9} Z'
        fins = f'M{cx - L * .02} {cy - Hh * .5} l{L * .06} {-Hh * .7} l{L * .04} {Hh * .64} Z M{cx + L * .26} {cy - Hh * .38} l{L * .05} {-Hh * .5} l{L * .03} {Hh * .48} Z'
        bars = ''.join(f'<path d="M{cx - L * .2 + k * L * .07} {cy - Hh * .5} l-6 {Hh * .6}" stroke="#2c4552" stroke-width="3" opacity=".5"/>' for k in range(7))
        out.append(f'<g opacity="{1 - i * .12:.2f}"><path d="{tail}" fill="#5f7d8c"/><path d="{fins}" fill="#5f7d8c"/><path d="{body}" fill="url(#es1)"/>{bars}{eye(nx + L * .12, cy - Hh * .1, Hh * .16, "#111", "#f2e9b8")}</g>')
    return scene('espeton', ''.join(out), floor='none', seed=15)


def tiburon_ballena():
    rnd = random.Random(17)
    body = 'M80 330 C90 270 160 240 260 236 C420 230 600 240 700 280 L800 300 L800 360 L700 372 C580 410 400 420 250 412 C150 406 86 380 80 330 Z'
    pat = (''.join(f'<path d="M{x} 240 L{x - 20} 410" stroke="#e6f1f4" stroke-width="3" opacity=".55"/>' for x in range(300, 800, 60))
           + ''.join(f'<circle cx="{rnd.uniform(150, 790):.0f}" cy="{rnd.uniform(245, 400):.0f}" r="{rnd.uniform(3.5, 7):.1f}" fill="#f2f8fa" opacity=".85"/>' for _ in range(120)))
    b = (f'<defs>{grad("wb", "#24485c", "#8aa3ae")}<clipPath id="wbc"><path d="{body}"/></clipPath></defs>' + shadow(420, 520, 330, 26)
         + '<path d="M470 240 C500 180 540 150 560 146 C560 190 550 220 540 250 Z" fill="#2a5064"/><path d="M300 380 C300 440 250 480 210 494 C230 450 250 410 260 390 Z" fill="#2a5064"/>'
         + f'<path d="{body}" fill="url(#wb)"/><g clip-path="url(#wbc)">{pat}</g><path d="M86 342 C120 352 180 352 214 344" stroke="#14303d" stroke-width="5" fill="none"/>'
         + eye(170, 312, 6, '#0a1418', '#c6d6dc')
         + ''.join(f'<path d="M{x} 300 q8 30 0 60" stroke="#14303d" stroke-width="3" fill="none" opacity=".6"/>' for x in (230, 246, 262, 278)))
    return scene('tiburon-ballena', b, tropical=True, floor='none', seed=17)


def manta():
    rnd = random.Random(19)
    wing = 'M400 220 C340 230 250 250 120 330 C220 350 320 350 380 380 C390 420 395 450 400 470 C405 450 410 420 420 380 C480 350 580 350 680 330 C550 250 460 230 400 220 Z'
    b = (f'<defs>{grad("mt", "#1d2a33", "#3c4e59")}<clipPath id="mtc"><path d="{wing}"/></clipPath></defs>' + shadow(400, 540, 260, 24)
         + '<path d="M400 465 C400 520 410 560 430 590" stroke="#1d2a33" stroke-width="5" fill="none"/>'
         + f'<path d="{wing}" fill="url(#mt)"/><g clip-path="url(#mtc)"><path d="M250 300 C300 270 340 262 380 266 C350 300 320 330 280 340 Z" fill="#e8eef0" opacity=".85"/><path d="M550 300 C500 270 460 262 420 266 C450 300 480 330 520 340 Z" fill="#e8eef0" opacity=".85"/>{spots(rnd, 300, 500, 300, 420, 10, 3, 6, "#e8eef0", .5)}</g>'
         + '<path d="M378 222 C370 196 372 178 382 170 C390 184 392 204 390 222 Z" fill="#26343d"/><path d="M422 222 C430 196 428 178 418 170 C410 184 408 204 410 222 Z" fill="#26343d"/>')
    return scene('manta', b, tropical=True, floor='none', seed=19)


def payaso():
    rnd = random.Random(21)
    tent = ''.join(f'<path d="M{x} 600 C{x + rnd.randint(-30, 30)} 520 {x + rnd.randint(-40, 40)} 470 {x + rnd.randint(-30, 30)} {rnd.randint(390, 450)}" stroke="#e7a7c4" stroke-width="13" fill="none" stroke-linecap="round" opacity=".95"/>'
                   f'<circle cx="0" cy="0" r="0"/>' for x in range(120, 700, 18))
    tips = ''.join(f'<circle cx="{rnd.randint(120, 700)}" cy="{rnd.randint(390, 450)}" r="8" fill="#f6d0e0"/>' for _ in range(30))
    bands = ''.join(f'<path d="M{x} 150 C{x + 20} 250 {x + 20} 350 {x} 450" stroke="#111" stroke-width="{w + 10}" fill="none"/><path d="M{x} 150 C{x + 20} 250 {x + 20} 350 {x} 450" stroke="#fafafa" stroke-width="{w}" fill="none"/>' for x, w in ((285, 30), (395, 34), (510, 22)))
    f = fish('p', 400, 290, 330, 190, '#f07a1c', '#f8a24a', '#ef7a20', tail='round', dorsal='long', pattern=bands)
    return scene('pez-payaso', tent + tips + f, tropical=True, floor='none', seed=21)


def pez_leon():
    rnd = random.Random(23)
    stripes = ''.join(f'<path d="M{x} 160 l-14 300" stroke="{"#a52a1f" if i % 2 else "#f4e6d4"}" stroke-width="15" opacity=".9"/>' for i, x in enumerate(range(220, 620, 16)))
    fan = lambda a, r: (f'M350 320 Q{350 + math.cos(math.radians(a - 12)) * r * .6:.0f} {320 + math.sin(math.radians(a - 12)) * r * .6:.0f} '
                        f'{350 + math.cos(math.radians(a)) * r:.0f} {320 + math.sin(math.radians(a)) * r:.0f}')
    fans = ''.join(f'<path d="{fan(a, 150 + (a % 20))}" stroke="#c94a38" stroke-width="5" fill="none" stroke-linecap="round"/>'
                   f'<path d="{fan(a, 150 + (a % 20))}" stroke="#f6e4d0" stroke-width="2" fill="none" stroke-dasharray="10 10"/>' for a in range(28, 100, 8))
    spines = ''.join(f'<path d="M{x} 222 Q{x + 22} {160 - (x % 3) * 8} {x + 30} {110 + (x % 3) * 16}" stroke="#c94a38" stroke-width="5" fill="none" stroke-linecap="round"/>'
                     f'<path d="M{x} 222 Q{x + 22} {160 - (x % 3) * 8} {x + 30} {110 + (x % 3) * 16}" stroke="#f6e4d0" stroke-width="2" fill="none" stroke-dasharray="8 8"/>' for x in range(300, 520, 22))
    f = fish('l', 410, 290, 360, 160, '#c9533d', '#f0d0b5', '#d8735c', tail='round', dorsal='soft', pattern=stripes)
    return scene('pez-leon', spines + f + fans, tropical=True, floor='reef', seed=23)


def tiburon_puntas():
    body = 'M120 300 C150 270 230 256 330 256 C470 256 590 270 650 292 L650 318 C590 340 470 350 330 348 C230 346 150 330 120 300 Z'
    b = (f'<defs>{grad("tb1", "#66808c", "#d6e0e4")}</defs>' + shadow(420, 520, 260, 20)
         + '<path d="M360 258 C380 200 410 170 430 164 C428 200 424 236 418 260 Z" fill="#6c8692"/><path d="M412 178 C420 170 428 166 430 164 C430 176 428 186 426 196 Z" fill="#fafafa"/>'
         + '<path d="M640 296 L760 210 C744 260 744 300 760 360 L640 316 Z" fill="#6c8692"/><path d="M742 222 L760 210 C756 226 752 238 750 248 Z" fill="#fafafa"/>'
         + '<path d="M300 340 C280 390 240 420 210 428 C226 392 246 362 262 344 Z" fill="#6c8692"/>'
         + f'<path d="{body}" fill="url(#tb1)"/><path d="M150 312 C190 322 240 324 280 318" stroke="#41565f" stroke-width="3" fill="none"/>'
         + ''.join(f'<path d="M{x} 286 q6 16 0 32" stroke="#41565f" stroke-width="2" fill="none"/>' for x in (230, 242, 254, 266, 278))
         + eye(170, 292, 6, '#0e1418', '#d9e2e6'))
    return scene('tiburon-puntas-blancas', b, tropical=True, floor='reef', seed=25)


def raya_aguila():
    rnd = random.Random(27)
    wing = 'M400 230 C360 236 270 250 140 320 C240 330 330 336 380 352 C390 380 396 400 400 410 C404 400 410 380 420 352 C470 336 560 330 660 320 C530 250 440 236 400 230 Z'
    b = (f'<defs>{grad("ra", "#24343e", "#41535e")}<clipPath id="rac"><path d="{wing}"/></clipPath></defs>' + shadow(400, 530, 260, 20)
         + '<path d="M400 405 C402 470 420 540 470 600" stroke="#24343e" stroke-width="4" fill="none"/>'
         + f'<path d="{wing}" fill="url(#ra)"/><g clip-path="url(#rac)">{spots(rnd, 150, 650, 240, 400, 70, 4, 8, "#f1f4f5", .95)}</g>'
         + '<path d="M384 232 C390 196 400 182 400 182 C400 182 410 196 416 232 Z" fill="#2c3d47"/>' + eye(388, 222, 5, '#0b1013', '#c9d4d8') + eye(412, 222, 5, '#0b1013', '#c9d4d8'))
    return scene('raya-aguila', b, tropical=True, floor='sand', seed=27)


def napoleon():
    lines = ''.join(f'<path d="M{170 + k * 6} {250 + k * 9} q30 -8 60 4" stroke="#1d4d4a" stroke-width="3" fill="none" opacity=".8"/>' for k in range(9))
    scales = ''.join(f'<path d="M{x} {y} q8 -8 16 0" stroke="#1b5c58" stroke-width="2" fill="none" opacity=".55"/>' for x in range(260, 620, 22) for y in range(200, 420, 22))
    hump = '<path d="M190 250 C200 170 260 150 300 170 C270 190 240 220 226 260 Z" fill="#2f8a7e"/>'
    f = fish('n', 400, 300, 440, 250, '#2f8a7e', '#7cc4b4', '#2a7a70', tail='round', dorsal='long', pattern=lines + scales, lips=True, extra=hump)
    return scene('napoleon', f, tropical=True, floor='reef', seed=29)


SPECIES = {
    'mero': mero, 'pulpo': pulpo, 'morena': morena, 'caballito': caballito, 'sepia': sepia, 'pez-luna': pez_luna,
    'tortuga-boba': lambda: tortuga('tortuga-boba', '#b0703a', '#6d4122', '#c99a6a', 1.15, 31),
    'espeton': espeton, 'tiburon-ballena': tiburon_ballena, 'manta': manta,
    'tortuga-verde': lambda: tortuga('tortuga-verde', '#6f7f3e', '#3d4a24', '#a7a77b', .95, 33),
    'pez-payaso': payaso, 'pez-leon': pez_leon, 'tiburon-puntas-blancas': tiburon_puntas, 'raya-aguila': raya_aguila, 'napoleon': napoleon,
}


def main(argv):
    from PIL import Image
    from playwright.sync_api import sync_playwright
    keep = Path(argv[argv.index('--svg') + 1]) if '--svg' in argv else None
    only = [a for a in argv if a in SPECIES]
    OUT.mkdir(parents=True, exist_ok=True)
    exe = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=exe) if Path(exe).exists() else p.chromium.launch()
        page = b.new_page(viewport={'width': W, 'height': H}, device_scale_factor=2)
        for key, fn in SPECIES.items():
            if only and key not in only: continue
            svg = fn()
            if keep: keep.mkdir(parents=True, exist_ok=True); (keep / f'{key}.svg').write_text(svg, encoding='utf-8')
            page.set_content(f'<html><body style="margin:0">{svg}</body></html>')
            png = page.screenshot(clip={'x': 0, 'y': 0, 'width': W, 'height': H})
            im = Image.open(io.BytesIO(png)).convert('RGB')
            for w in WIDTHS:
                im.resize((w, w * 3 // 4), Image.LANCZOS).save(OUT / f'{key}-{w}.webp', 'WEBP', quality=82, method=6)
            print(key, sum((OUT / f'{key}-{w}.webp').stat().st_size for w in WIDTHS) // 1024, 'KB')
        b.close()


if __name__ == '__main__':
    main(sys.argv[1:])
