"""v50.57 (revisión general, 5.2 y 5.3): what the load test of 300 people and 20 bookings a second found.

- The outbox written to files (development and the DEMO package) kept the write lock of the database while it built
  up to 150 emails with their QR: up to 2 s in which no booking, payment or visit could be saved.
- Far above that load (from about 35 to 70 bookings a second, depending on the processor) a booking waited more than
  10 s to write and answered «Error interno»: now it says what happened (503) and nothing is left half done.
"""
import json
import sqlite3
import subprocess
import sys
import unittest

from helpers import Server, ServerTestCase, ROOT


class SpoolWithoutLock(unittest.TestCase):
    def test_outbox_to_files_does_not_hold_the_write_lock(self):
        srv = Server().start(); srv.stop(cleanup=False)   # a database with its schema and no server writing at the same time
        try:
            code = '''
import json, sqlite3, sys
sys.path.insert(0, %r)
import server
db = server.connect()
for i in range(6):
    server.queue_email(db, 'booking_confirmed', f'cola{i}@diver.example.org', 'Cola', server.sample_email_ctx('booking_confirmed'), 'es', ('booking', 1))
db.commit(); db.close()
free = []
build = server._build_message
def building(cfg, row):
    # while each email is built: can somebody else (a booking) write?
    other = sqlite3.connect(str(server.DB_PATH), timeout=0)
    try:
        other.execute('BEGIN IMMEDIATE'); other.rollback(); free.append(True)
    except sqlite3.OperationalError:
        free.append(False)
    finally:
        other.close()
    return build(cfg, row)
server._build_message = building
print(json.dumps({'n': server.spool_outbox_to_files(limit=50), 'free': free}))
''' % str(ROOT / 'app')
            r = subprocess.run([sys.executable, '-c', code], env=srv.env, cwd=str(srv.tmp), capture_output=True, text=True, timeout=120)
            self.assertEqual(r.returncode, 0, r.stderr)
            out = json.loads(r.stdout.strip().splitlines()[-1])
            self.assertEqual(out['n'], 6)
            self.assertEqual(out['free'], [True] * 6, 'the write lock was held while the emails were being built')
            rows = srv.sql("SELECT status, delivery FROM email_outbox WHERE to_email LIKE 'cola%@diver.example.org'")
            self.assertEqual(len(rows), 6)
            self.assertTrue(all(x['status'] == 'sent' and x['delivery'] == 'file' for x in rows), rows)
            self.assertEqual(len(list((srv.tmp / 'mail').glob('*booking_confirmed*cola*.eml'))), 6)
        finally:
            srv.stop()


class LockedDatabase(ServerTestCase):
    extra_env = {'WOD_DB_BUSY_MS': '300'}   # the wait for another write (10 s by default) made short for the test

    def test_a_locked_database_answers_503_and_the_retry_books(self):
        admin = self.make_admin()
        center = self.make_center(admin, 'bloqueo')
        cid = center.user['center_id']
        sid = center.post('/api/provider-services', {'title': 'Salida de la prueba', 'price': 30, 'booking_mode': 'request'}).json['id']
        slot = center.post('/api/provider-services/slot', {'service_id': sid, 'slot_date': '2031-03-12', 'slot_time': '09:00', 'spots_total': 6}).json['slot_id']
        diver = self.make_diver('bloqueo')
        body = {'center_id': cid, 'service_id': sid, 'slot_id': slot, 'participants': 1}
        before = self.server.sql('SELECT COUNT(*) AS n FROM bookings')[0]['n']
        other = sqlite3.connect(str(self.server.db), timeout=5)
        other.execute('BEGIN IMMEDIATE')   # somebody else is writing for longer than the wait
        try:
            r = diver.post('/api/bookings', body)
        finally:
            other.rollback(); other.close()
        self.assertEqual(r.status, 503, r)
        self.assertEqual(r.json['error'], 'Ahora mismo hay demasiadas operaciones a la vez y no se ha podido guardar. Vuelve a intentarlo en unos segundos.')
        self.assertEqual(self.server.sql('SELECT COUNT(*) AS n FROM bookings')[0]['n'], before)   # nothing half done
        self.assertEqual(self.server.sql('SELECT spots_available FROM service_slots WHERE id=?', (slot,))[0]['spots_available'], 6)
        r = diver.post('/api/bookings', body)   # the same booking again, with the database free: it is made
        self.assertEqual(r.status, 200, r)
        self.assertEqual(self.server.sql('SELECT COUNT(*) AS n FROM bookings')[0]['n'], before + 1)


if __name__ == '__main__':
    unittest.main()
