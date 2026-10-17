"""v50.57 · Revisión general (15/10/2026), Bloque 1.1: «No time zone found with key Europe/Madrid».

Windows has no time zones of its own: Python reads them from the «tzdata» package. Without it every ZoneInfo() failed (a
KeyError, answered as «Falta un dato obligatorio») and the panel of the centres and the bookings, planning and agenda of
the freelances did not open.

- SinZonasHorarias: the server started as on a clean Windows (no time zones of the system and a tzdata that brings
  nothing). The panel, bookings, planning and agenda of a centre and of a freelance answer, a booking can be made, and
  «Estado del sistema» says what is missing and how to fix it.
- ZonaGuardadaMal: a time zone saved wrong in a service or an agenda never breaks a screen: the zone of the country is
  used, the log says it and «Estado del sistema» lists it.
- Arranque: tzdata is pinned in requirements.txt, the official start installs it and checks it before starting.
"""
from __future__ import annotations

import datetime as dt
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import IN_PERSON, ROOT, ServerTestCase  # noqa: E402

DAY = (dt.date.today() + dt.timedelta(days=12)).isoformat()


def windows_without_tzdata() -> tuple[dict, Path]:
    """Environment of a Python that finds no time zone at all: an empty search path for the system ones and, first in the
    path, a «tzdata» package that brings no data (it hides the real one if it is installed)."""
    tmp = Path(tempfile.mkdtemp(prefix='wod-sin-zonas-'))
    (tmp / 'vacio').mkdir()
    (tmp / 'falso' / 'tzdata').mkdir(parents=True)
    (tmp / 'falso' / 'tzdata' / '__init__.py').write_text('', encoding='utf-8')
    return {'PYTHONTZPATH': str(tmp / 'vacio'), 'PYTHONPATH': str(tmp / 'falso')}, tmp


class SinZonasHorarias(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        env, cls.tmp = windows_without_tzdata()
        probe = subprocess.run([sys.executable, '-c', 'from zoneinfo import ZoneInfo; ZoneInfo("Europe/Madrid")'], env={**env, 'PATH': '/usr/bin:/bin'}, capture_output=True)
        assert probe.returncode != 0, 'the simulated Windows still finds the time zones'
        cls.extra_env = dict(cls.extra_env, PYTHONUNBUFFERED='1', **env)
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center = t.make_center(cls.admin, 'sinzona')
        cls.pro = t.make_freelance(cls.admin, 'sinzona')
        cls.diver = t.make_diver('sinzona')
        cls.sid = cls.center.post('/api/provider-services', {'title': 'Inmersión sin zonas', 'price': 40, 'booking_mode': 'request', 'max_participants': 6}).json['id']
        cls.slot = cls.center.post('/api/provider-services/slot', {'service_id': cls.sid, 'slot_date': DAY, 'slot_time': '10:00', 'spots_total': 6}).json['slot_id']
        cls.day_sid = cls.pro.post('/api/provider-services', {'title': 'Guía por días', 'price': 120, 'booking_mode': 'request', 'booking_unit': 'day', 'max_participants': 2,
                                                              'pricing': {'day': 120}, **IN_PERSON}).json['id']

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass(); shutil.rmtree(cls.tmp, ignore_errors=True)

    def ok(self, client, path):
        r = client.get(path)
        self.assertEqual(r.status, 200, f'{path}: {r.status} {r.json}')
        self.assertNotIn('No time zone', str(r.json)); self.assertNotIn('Falta un dato obligatorio', str(r.json))
        return r.json

    def test_1_se_puede_reservar(self):
        r = self.diver.post('/api/bookings', {'center_id': self.center.user['center_id'], 'service_id': self.sid, 'slot_id': self.slot, 'participants': 1})
        self.assertEqual(r.status, 200, r.json)
        r = self.diver.post('/api/bookings', {'service_id': self.day_sid, 'days': [DAY], 'part': 'full', 'participants': 1, 'in_person_ack': True})
        self.assertEqual(r.status, 200, r.json)

    def test_2_panel_del_centro(self):
        month = DAY[:7]
        for path in (f"/api/centers/{self.center.user['center_id']}", '/api/bookings', f"/api/provider-services?provider_id={self.center.user['id']}",
                     '/api/center/clients', '/api/center/analytics', '/api/provider/experiences', '/api/center/requests',
                     f'/api/center/planning?month={month}', '/api/bookings?payment=required&limit=500', f'/api/manifest/day?date={dt.date.today().isoformat()}',
                     '/api/provider/stats?days=30', '/api/center/activity', '/api/me'):
            with self.subTest(path): self.ok(self.center, path)
        planning = self.ok(self.center, f'/api/center/planning?month={month}')
        self.assertTrue(any(s.get('slot_date') == DAY for s in planning.get('slots', [])), planning)

    def test_3_reservas_planning_y_agenda_del_freelance(self):
        month = DAY[:7]
        for path in ('/api/bookings', f'/api/center/planning?month={month}', f'/api/agenda/mine?month={month}', '/api/center/requests',
                     f'/api/agenda/public?service={self.day_sid}&month={month}', '/api/provider/stats?days=30', '/api/me'):
            with self.subTest(path): self.ok(self.pro, path)

    def test_4_el_buceador_ve_su_reserva(self):
        area = self.ok(self.diver, '/api/me/area')
        self.assertTrue(area['bookings'])

    def test_5_estado_del_sistema_dice_que_falta_y_como_arreglarlo(self):
        h = self.ok(self.admin, '/api/admin/health')
        row = next(x for x in h['services'] if x['key'] == 'timezones')
        self.assertEqual(row['state'], 'error'); self.assertIn('tzdata', row['detail']); self.assertIn('iniciar.bat', row['detail'])

    def test_6_la_consola_lo_dice_al_arrancar(self):
        out = (self.server.tmp / 'stdout.log').read_text(encoding='utf-8')
        self.assertIn('faltan las zonas horarias', out.lower()); self.assertIn('pip install -r requirements.txt', out)


class ZonaGuardadaMal(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center = t.make_center(cls.admin, 'zonamal')
        cls.pro = t.make_freelance(cls.admin, 'zonamal')
        cls.sid = cls.center.post('/api/provider-services', {'title': 'Salida con zona rota', 'price': 40, 'booking_mode': 'request', 'max_participants': 6}).json['id']
        cls.slot = cls.center.post('/api/provider-services/slot', {'service_id': cls.sid, 'slot_date': DAY, 'slot_time': '10:00', 'spots_total': 6}).json['slot_id']
        cls.day_sid = cls.pro.post('/api/provider-services', {'title': 'Días con zona rota', 'price': 120, 'booking_mode': 'request', 'booking_unit': 'day', 'max_participants': 2,
                                                              'pricing': {'day': 120}, **IN_PERSON}).json['id']
        cls.pro.get(f'/api/agenda/mine?month={DAY[:7]}')   # creates the freelance's own agenda
        # saved wrong (an old import, a hand edit): the API never lets it in
        cls.server.sql("UPDATE provider_services SET timezone='Europe/Madird' WHERE id IN (?,?)", (cls.sid, cls.day_sid))
        cls.server.sql("UPDATE resources SET timezone='Hora/Inventada' WHERE owner_user_id=?", (cls.pro.user['id'],))

    def test_nada_se_rompe_y_se_usa_la_del_pais(self):
        r = self.center.get(f'/api/center/planning?month={DAY[:7]}'); self.assertEqual(r.status, 200, r.json)
        r = self.pro.get(f'/api/agenda/mine?month={DAY[:7]}'); self.assertEqual(r.status, 200, r.json)
        self.assertEqual(r.json['resource']['timezone'], 'Europe/Madrid')   # the freelance's country (Spain by default)
        r = self.client().get(f'/api/agenda/public?service={self.day_sid}&month={DAY[:7]}'); self.assertEqual(r.status, 200, r.json)
        self.assertEqual(r.json['timezone'], 'Europe/Madrid')
        diver = self.make_diver('zonamal')
        r = diver.post('/api/bookings', {'center_id': self.center.user['center_id'], 'service_id': self.sid, 'slot_id': self.slot, 'participants': 1}); self.assertEqual(r.status, 200, r.json)

    def test_estado_del_sistema_y_registro(self):
        self.center.get(f'/api/center/planning?month={DAY[:7]}'); self.pro.get(f'/api/agenda/mine?month={DAY[:7]}')
        h = self.admin.get('/api/admin/health').json
        self.assertEqual(next(x for x in h['services'] if x['key'] == 'timezones')['state'], 'ok')
        row = next(x for x in h['services'] if x['key'] == 'timezones_saved')
        self.assertEqual(row['state'], 'error')
        for txt in ('Salida con zona rota', 'Europe/Madird', 'Hora/Inventada', 'la del país'): self.assertIn(txt, row['detail'])
        self.assertIn('zona_horaria_no_valida', (self.server.tmp / 'stderr.log').read_text(encoding='utf-8'))


class Arranque(unittest.TestCase):
    def test_tzdata_fijado_e_instalado_por_los_arranques(self):
        req = (ROOT / 'requirements.txt').read_text(encoding='utf-8')
        self.assertRegex(req, r'(?m)^tzdata==\d{4}\.\d+\s')
        start = (ROOT / 'scripts' / 'iniciar.py').read_text(encoding='utf-8')
        self.assertIn("'tzdata': 'tzdata'", start)                 # installed when missing, like the others
        self.assertIn('check_time_zones()', start)                  # and checked before the server starts
        for f in ('iniciar.bat', 'iniciar.sh'): self.assertIn('scripts', (ROOT / f).read_text(encoding='utf-8'))

    def test_el_codigo_no_usa_zoneinfo_directamente(self):
        # every zone goes through wod.agenda.zone(), which never fails
        for p in [ROOT / 'app' / 'server.py', *(ROOT / 'app' / 'wod').glob('*.py')]:
            if p.name == 'agenda.py': continue
            self.assertNotIn('ZoneInfo(', p.read_text(encoding='utf-8'), p.name)


if __name__ == '__main__':
    unittest.main()
