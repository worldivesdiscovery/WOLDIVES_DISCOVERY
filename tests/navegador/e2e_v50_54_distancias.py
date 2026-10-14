#!/usr/bin/env python3
"""v50.54 · punto 5: distancias correctas o ninguna, en un navegador real (Chromium) con la ubicación simulada.

- Jávea con ubicación precisa (± 20 m): Top 10 y «Puntos de buceo» muestran Cabo San Antonio a menos de 15 km.
- Dénia con ubicación precisa: también a menos de 15 km.
- Jávea con ubicación aproximada (± 20 km, como la que da el navegador por la IP o la «ubicación aproximada» de
  Android): mismos puntos y mismo orden, ningún kilómetro y el aviso «ubicación aproximada».
- Madrid aproximada (lo que causaba «556 km»): ningún kilómetro.
- Una zona elegida: sin kilómetros.

    python3 tests/navegador/e2e_v50_54_distancias.py [carpeta-de-capturas]
"""
from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1])]
from helpers import Server  # noqa: E402
from e2e_markers import chromium  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

JAVEA = (38.7893, 0.1662)
DENIA = (38.8408, 0.1057)
MADRID = (40.4168, -3.7038)
CABO = 'Cabo San Antonio'


def km_of(text):
    m = re.search(r'([\d.,]+)\s*km', text or '')
    return float(m.group(1).replace('.', '').replace(',', '.')) if m else None


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(tempfile.mkdtemp(prefix='wod-e2e-dist-'))
    out.mkdir(parents=True, exist_ok=True)
    srv = Server().start()
    rows, problems = [], []
    try:
        with sync_playwright() as pw:
            browser = chromium(pw)
            errors = []

            def page_at(pos, acc, size=(1366, 900)):
                ctx = browser.new_context(viewport={'width': size[0], 'height': size[1]}, locale='es-ES', permissions=['geolocation'],
                                          geolocation={'latitude': pos[0], 'longitude': pos[1], 'accuracy': acc})
                pg = ctx.new_page()
                pg.on('pageerror', lambda e: errors.append(str(e)))
                # map tiles from outside are blocked by the proxy of the test machine (not an error of the web)
                pg.on('console', lambda m: errors.append(m.text) if m.type == 'error' and 'ERR_TUNNEL_CONNECTION_FAILED' not in m.text else None)
                return ctx, pg

            def top10(pos, acc, shot=None):
                ctx, pg = page_at(pos, acc)
                pg.goto(srv.base + '/#/top10'); pg.wait_for_selector('#tt-list .tt-card:not(.is-skeleton)', timeout=20000); pg.wait_for_timeout(400)
                cards = pg.evaluate("[...document.querySelectorAll('#tt-list .tt-card')].map(c=>({name:c.querySelector('h3')?.textContent.trim(),km:c.querySelector('.tt-dist')?.textContent||''}))")
                sub = pg.inner_text('#tt-sub')
                if shot: pg.screenshot(path=str(out / shot))
                ctx.close(); return cards, sub

            def puntos(pos, acc, shot=None):
                ctx, pg = page_at(pos, acc)
                pg.goto(srv.base + '/#/puntos'); pg.wait_for_timeout(600)
                btn = pg.locator('#pt-near, [data-near], button:has-text("Cerca de mí"), button:has-text("Usar mi ubicación")').first
                if btn.count(): btn.click()
                pg.wait_for_timeout(1500)
                cards = pg.evaluate("[...document.querySelectorAll('.pt-card')].map(c=>({name:(c.querySelector('h3,h2')?.textContent||'').trim(),km:c.querySelector('.pt-dist')?.textContent||''}))")
                note = pg.evaluate("document.querySelector('#pt-locbar,.pt-locbar')?.textContent||''")
                if shot: pg.screenshot(path=str(out / shot))
                ctx.close(); return cards, note

            # 1) precise: Jávea and Dénia
            for label, pos in (('Jávea', JAVEA), ('Dénia', DENIA)):
                cards, sub = top10(pos, 20, f'top10-{label.lower()}-precisa.png' if label == 'Jávea' else None)
                cabo = next((c for c in cards if c['name'] == CABO), None)
                k = km_of(cabo['km']) if cabo else None
                ok = k is not None and k < 15 and all(km_of(c['km']) is not None for c in cards)
                rows.append((f'Top 10 desde {label} (± 20 m)', f"{CABO}: {cabo['km'] if cabo else 'no está en la lista'}", ok))
                if not ok: problems.append(f'Top 10 {label}: {cards}')
            cards, note = puntos(JAVEA, 20, 'puntos-javea-precisa.png')
            cabo = next((c for c in cards if c['name'] == CABO), None)
            k = km_of(cabo['km']) if cabo else None
            ok = k is not None and k < 15
            rows.append(('Puntos de buceo desde Jávea (± 20 m)', f"{CABO}: {cabo['km'] if cabo else 'no está'} · {len(cards)} tarjetas", ok))
            if not ok: problems.append(f'Puntos Jávea: {cards[:6]}')

            # 2) approximate: same order, no km, and it says why
            precise_names = [c['name'] for c in top10(JAVEA, 20)[0]]
            cards, sub = top10(JAVEA, 20000, 'top10-javea-aproximada.png')
            ok = all(not c['km'] for c in cards) and [c['name'] for c in cards] == precise_names and 'aproximada' in sub
            rows.append(('Top 10 desde Jávea (± 20 km)', f'{len(cards)} buceos, sin km; «{sub.strip()}»', ok))
            if not ok: problems.append(f'Top 10 aproximada: {cards} / {sub}')
            cards, note = puntos(JAVEA, 20000, 'puntos-javea-aproximada.png')
            ok = cards and all(not c['km'] for c in cards)
            rows.append(('Puntos de buceo desde Jávea (± 20 km)', f'{len(cards)} tarjetas sin km; «{note.strip()[:80]}»', bool(ok)))
            if not ok: problems.append(f'Puntos aproximada: {cards[:4]}')
            cards, sub = top10(MADRID, 30000)
            ok = all(not c['km'] for c in cards)
            rows.append(('Top 10 con la IP en Madrid (± 30 km)', 'ningún km' if ok else str(cards[:3]), ok))
            if not ok: problems.append('Madrid aproximada con km')

            # 3) a chosen zone: no km
            ctx, pg = page_at(JAVEA, 20)
            pg.goto(srv.base + '/#/top10'); pg.wait_for_selector('#tt-zones .cd-chip', timeout=20000)
            pg.locator('#tt-zones .cd-chip').first.click(); pg.wait_for_timeout(1500)
            kms = pg.evaluate("[...document.querySelectorAll('#tt-list .tt-dist')].length")
            rows.append(('Top 10 de una zona elegida', 'sin km' if kms == 0 else f'{kms} distancias', kms == 0))
            if kms: problems.append('zona con km')
            ctx.close()
            browser.close()
            if errors: problems.append('errores en la consola: ' + ' | '.join(errors[:4]))
    finally:
        srv.stop()
    for what, got, ok in rows: print(f"{'OK ' if ok else 'MAL'} {what:42} {got}")
    print(f'Capturas en {out}')
    if problems:
        print('PROBLEMAS:\n - ' + '\n - '.join(problems)); sys.exit(1)
    print('OK: distancias correctas con ubicación precisa y ninguna con ubicación aproximada o zona elegida.')


if __name__ == '__main__':
    main()
