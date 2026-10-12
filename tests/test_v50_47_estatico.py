"""v50.47 · parte B.2: prueba estática de las consultas a datos de centro.

Ninguna sentencia SQL nueva puede leer o cambiar una tabla de centro sin filtrar por centro en el propio SQL, salvo
dentro de la capa de inquilinos (app/wod/inquilinos.py), que añade siempre el filtro. Las sentencias heredadas que leen
una fila por su id después de comprobar en el código que es del centro de la sesión están en una lista revisada
(docs/seguridad/sql-sin-filtro.json) que solo puede acortarse: si aparece una sentencia sin filtro que no está en la
lista, esta prueba falla."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts' / 'seguridad'))
import sql_centros  # noqa: E402


class TenantSql(unittest.TestCase):
    def test_no_new_unfiltered_sql_on_tenant_tables(self):
        reviewed = json.loads(sql_centros.REVIEWED.read_text(encoding='utf-8'))['sentencias']
        bad = sql_centros.unfiltered(sql_centros.classify())
        new = [f"{r['file']}:{r['line']} {r['sql'][:160]}" for r in bad if r['key'] not in reviewed]
        self.assertEqual(new, [], 'SQL nueva sobre tablas de centro sin filtrar por centro: usa wod.inquilinos (get_slot, get_booking…) o añade el filtro')

    def test_reviewed_list_only_shrinks(self):
        """A reviewed statement that no longer exists must leave the list (the list never hides new code)."""
        reviewed = json.loads(sql_centros.REVIEWED.read_text(encoding='utf-8'))['sentencias']
        current = {r['key'] for r in sql_centros.unfiltered(sql_centros.classify())}
        gone = sorted(set(reviewed) - current)
        self.assertEqual(gone, [], 'Quita de docs/seguridad/sql-sin-filtro.json las sentencias que ya no existen: python scripts/seguridad/sql_centros.py --revisada')

    def test_the_layer_always_filters(self):
        layer = (ROOT / 'app' / 'wod' / 'inquilinos.py').read_text(encoding='utf-8')
        for fn in ('def get_service', 'def get_slot', 'def get_booking', 'def slot_bookings'):
            body = layer.split(fn, 1)[1].split('\ndef ', 1)[0]
            self.assertIn('owner_filter(ctx', body, fn)
            self.assertIn('NotFound', body if fn != 'def slot_bookings' else layer.split('def get_slot', 1)[1].split('\ndef ', 1)[0], fn)

    def test_detector_catches_an_unfiltered_query(self):
        """The detector itself: a query on bookings by id only is «sin filtro»; with the centre it is filtered."""
        import ast
        tree = ast.parse("db.execute('SELECT * FROM bookings WHERE id=?', (1,))\ndb.execute('SELECT * FROM bookings WHERE id=? AND center_id=?', (1, 2))")
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
        texts = [sql_centros._sql_of(c.args[0]) for c in calls if c.args]
        flags = [bool(sql_centros.FILTERS.search(t)) for t in texts]
        self.assertEqual(flags, [False, True])


if __name__ == '__main__':
    unittest.main()
