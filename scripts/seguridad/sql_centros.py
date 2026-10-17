"""Inventory of the SQL that touches the private tables of the centres (v50.47, encargo «aislamiento», parte B.2).

Every statement passed to .execute() in app/ is read with the Python parser (not with text searches). A statement that
touches a tenant table is «filtered» when its text restricts it to one tenant (provider_id, the centre column, the
freelance column, the payee, or a WHERE fragment built by the tenant layer); otherwise it is «sin filtro».

The test tests/test_v50_47_estatico.py fails when a statement «sin filtro» appears that is not in the reviewed list
docs/seguridad/sql-sin-filtro.json (ratchet: the list can only get shorter). The tenant layer (app/wod/inquilinos.py)
is the only module allowed to read tenant tables by id, because it always adds the filter itself.

  python scripts/seguridad/sql_centros.py              → summary
  python scripts/seguridad/sql_centros.py --lista      → every statement «sin filtro»
  python scripts/seguridad/sql_centros.py --revisada   → rewrites the reviewed list (only after reviewing each new line)
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REVIEWED = ROOT / 'docs' / 'seguridad' / 'sql-sin-filtro.json'
LAYER = 'app/wod/inquilinos.py'
TENANT_TABLES = ('provider_services', 'service_slots', 'bookings', 'boats', 'waiver_templates', 'travel_experiences', 'info_requests', 'resources',
                 'payment_orders', 'payment_refunds', 'center_tariffs', 'center_extras', 'center_equipment', 'center_integrations', 'center_members',
                 'center_links', 'data_shares', 'promotions', 'qr_codes', 'team_invites', 'experience_bookings', 'manifest_entries', 'slot_groups',
                 'slot_cancel_offers', 'reschedule_requests', 'waiver_signatures', 'notice_batches', 'notice_outbox', 'whatsapp_accounts',
                 'provider_settings', 'slot_events', 'resource_blocks', 'short_links')
FILTERS = re.compile(r"provider_id|center_id\s*(=|IN\b|IS NULL)|provider_user_id\s*=|payee_id\s*=|owner_center_id\s*=|owner_user_id\s*=|user_id\s*=\s*\?"
                     r"|\{(w|ew|where|scope|own|sw|bw|svc_where|bk_where|cond|flt|tenant|pw|rw)[^}]*\}|guest_center_id\s*=|recipient_user_id\s*=", re.I)
# pw and rw (v50.57): the centre or freelance of the session in the exports (bookings and resources), built from provider_ref
TABLE_RX = re.compile(r'\b(FROM|JOIN|INTO|UPDATE|TABLE)\s+(' + '|'.join(TENANT_TABLES) + r')\b', re.I)


def _sql_of(node):
    """The text of a str or f-string argument (expressions become {name})."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str): return node.value
    if isinstance(node, ast.JoinedStr):
        out = []
        for v in node.values:
            if isinstance(v, ast.Constant): out.append(str(v.value))
            else: out.append('{' + (ast.unparse(v.value) if hasattr(ast, 'unparse') else 'x') + '}')
        return ''.join(out)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        a, b = _sql_of(node.left), _sql_of(node.right)
        return (a or '{x}') + (b or '{x}') if (a or b) else None
    return None


def statements(root=ROOT):
    for f in sorted((root / 'app').rglob('*.py')):
        rel = f.relative_to(root).as_posix()
        tree = ast.parse(f.read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in ('execute', 'executemany') and node.args:
                sql = _sql_of(node.args[0])
                if sql: yield rel, node.lineno, sql


def normalise(sql):
    return re.sub(r'\s+', ' ', sql).strip()


def key_of(rel, sql):
    return hashlib.sha256((rel + '\n' + normalise(sql)).encode()).hexdigest()[:16]


def classify(root=ROOT):
    rows = []
    for rel, line, sql in statements(root):
        tables = sorted({m.group(2).lower() for m in TABLE_RX.finditer(sql)})
        if not tables: continue
        if re.match(r'\s*(CREATE|ALTER|DROP|PRAGMA)\b', sql, re.I) or 'sqlite_master' in sql: continue
        filtered = bool(FILTERS.search(sql))
        rows.append({'file': rel, 'line': line, 'tables': tables, 'filtered': filtered, 'layer': rel == LAYER, 'key': key_of(rel, sql), 'sql': normalise(sql)[:240]})
    return rows


def unfiltered(rows):
    return [r for r in rows if not r['filtered'] and not r['layer']]


def main(argv):
    rows = classify()
    bad = unfiltered(rows)
    if '--revisada' in argv:
        REVIEWED.parent.mkdir(parents=True, exist_ok=True)
        REVIEWED.write_text(json.dumps({'nota': 'Sentencias SQL sobre tablas de centro sin filtro por centro en el propio SQL, revisadas una a una: '
                                        'leen o cambian una fila por su id DESPUÉS de comprobar en el código que es del centro de la sesión '
                                        '(can_manage_booking, owns_service, manifest_slot…), o son tareas de sistema que recorren todos los '
                                        'centros y toman el centro de cada fila. La lista solo puede acortarse (prueba tests/test_v50_47_estatico.py).',
                                        'sentencias': {r['key']: f"{r['file']}:{r['line']} {r['sql'][:160]}" for r in bad}}, ensure_ascii=False, indent=1), encoding='utf-8')
        print(f'Lista revisada: {len(bad)} sentencias.'); return 0
    if '--lista' in argv:
        for r in bad: print(f"{r['file']}:{r['line']} [{','.join(r['tables'])}] {r['sql'][:200]}")
    print(f"{len(rows)} sentencias sobre tablas de centro: {sum(r['filtered'] for r in rows)} con filtro por centro, "
          f"{sum(r['layer'] for r in rows)} en la capa, {len(bad)} sin filtro (revisadas en {REVIEWED.relative_to(ROOT)}).")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
