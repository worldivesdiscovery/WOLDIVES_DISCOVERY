"""v50.52 · despliegue en Hostinger KVM 2 (encargo del 14/10/2026): dominio worlddivesdiscovery.com, proxy, cortafuegos,
antivirus comprobado de verdad, registros para Better Stack y el comprobador de la lista de lanzamiento. Lo que necesita
programas del VPS (caddy, ufw, clamd, vector, systemd) se prueba cuando están instalados y se salta si no."""
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app'))
from helpers import ServerTestCase  # noqa: E402

DESPLIEGUE = ROOT / 'docs' / 'despliegue'


def checker():
    spec = importlib.util.spec_from_file_location('comprobar_lanzamiento', ROOT / 'scripts' / 'despliegue' / 'comprobar_lanzamiento.py')
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


UFW_OK = """Status: active
Logging: on (low)
Default: deny (incoming), deny (outgoing), deny (routed)
New profiles: skip

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW IN    203.0.113.10               # SSH (IP conocida)
80/tcp                     ALLOW IN    Anywhere                   # web: http
443/tcp                    ALLOW IN    Anywhere                   # web: https
443/udp                    ALLOW IN    Anywhere                   # web: https HTTP/3
53                         ALLOW OUT   Anywhere                   # DNS
123/udp                    ALLOW OUT   Anywhere                   # NTP (hora)
67/udp                     ALLOW OUT   Anywhere                   # DHCP
443/tcp                    ALLOW OUT   Anywhere                   # HTTPS
80/tcp                     ALLOW OUT   Anywhere                   # HTTP: apt
587/tcp                    ALLOW OUT   Anywhere                   # correo
80/tcp (v6)                ALLOW IN    Anywhere (v6)              # web: http
"""


class Dominio(unittest.TestCase):
    """El dominio real es worlddivesdiscovery.com; www va a la raíz y pruebas.* está aparte y con contraseña."""

    def test_no_reference_to_the_old_domain_where_it_matters(self):
        places = [ROOT / 'app' / 'server.py', ROOT / '.env.example', ROOT / 'movil' / 'capacitor.config.json',
                  ROOT / 'movil' / 'android' / 'app' / 'src' / 'main' / 'assets' / 'capacitor.config.json', ROOT / 'movil' / 'www' / 'index.html',
                  *DESPLIEGUE.glob('*')]
        for p in places:
            if p.is_file():
                self.assertNotRegex(p.read_text(encoding='utf-8', errors='replace'), r'(?<![a-z])worldives\.com', str(p))
        self.assertIn('"url": "https://worlddivesdiscovery.com"', (ROOT / 'movil' / 'capacitor.config.json').read_text(encoding='utf-8'))

    def test_caddyfile(self):
        c = (DESPLIEGUE / 'Caddyfile').read_text(encoding='utf-8')
        self.assertRegex(c, r'(?m)^www\.worlddivesdiscovery\.com \{\n[^}]*redir https://worlddivesdiscovery\.com\{uri\} permanent')
        self.assertRegex(c, r'(?m)^pruebas\.worlddivesdiscovery\.com \{[\s\S]*?basic_auth[\s\S]*?reverse_proxy 127\.0\.0\.1:8001')
        self.assertIn('http://pruebas.worlddivesdiscovery.com', c)                      # /api by http: 403 there too
        caddy = shutil.which('caddy')
        if not caddy: self.skipTest('caddy no está instalado aquí')
        r = subprocess.run([caddy, 'validate', '--config', str(DESPLIEGUE / 'Caddyfile'), '--adapter', 'caddyfile'], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_systemd_units(self):
        prod = (DESPLIEGUE / 'worldives.service').read_text(encoding='utf-8')
        test = (DESPLIEGUE / 'worldives-pruebas.service').read_text(encoding='utf-8')
        self.assertIn('IPAddressDeny=10.0.0.0/8 172.16.0.0/12 192.168.0.0/16 169.254.0.0/16', prod)
        self.assertIn('User=worldives-pruebas', test); self.assertNotIn('/opt/worldives/', test)


class Cortafuegos(unittest.TestCase):
    """V13.2.5: entrada 22, 80 y 443; salida solo DNS, hora, HTTPS, HTTP (apt) y correo."""

    def test_script(self):
        s = (ROOT / 'scripts' / 'despliegue' / 'cortafuegos.sh').read_text(encoding='utf-8')
        self.assertIn('ufw default deny outgoing', s); self.assertIn('ufw default deny incoming', s)
        self.assertEqual(subprocess.run(['bash', '-n', str(ROOT / 'scripts' / 'despliegue' / 'cortafuegos.sh')]).returncode, 0)
        allowed_out = set(re.findall(r"ufw allow out \"?\$?\{?(\w+)", s))
        self.assertEqual(allowed_out, {'53', '123', '67', '443', '80', 'SMTP_PUERTO'})

    def test_checker_reads_ufw(self):
        m = checker()
        self.assertTrue(m.firewall_ok(UFW_OK))
        self.assertEqual(m.parse_ufw(UFW_OK)[2], [22, 80, 443])
        self.assertFalse(m.firewall_ok(UFW_OK.replace('deny (outgoing)', 'allow (outgoing)')))
        self.assertFalse(m.firewall_ok(UFW_OK + '3306/tcp                   ALLOW IN    Anywhere\n'))
        self.assertFalse(m.firewall_ok(UFW_OK.replace('Status: active', 'Status: inactive')))

    def test_checker_reads_sshd_and_keys(self):
        m = checker()
        good = 'port 22\npermitrootlogin no\npasswordauthentication no\nkbdinteractiveauthentication no\npubkeyauthentication yes\n'
        self.assertTrue(m.ssh_ok(m.parse_sshd(good)))
        self.assertFalse(m.ssh_ok(m.parse_sshd(good.replace('permitrootlogin no', 'permitrootlogin without-password'))))
        self.assertFalse(m.ssh_ok(m.parse_sshd(good.replace('passwordauthentication no', 'passwordauthentication yes'))))
        self.assertTrue(m.key_problem('K', 'x' * 40, []))
        self.assertTrue(m.key_problem('K', 'corta', []))
        k = 'a8F3kL0pQ2zX9vB7nM4cR1tY6uI5oP0w'
        self.assertEqual(m.key_problem('K', k, []), '')
        self.assertTrue(m.key_problem('K', k, [k]))


class Antivirus(unittest.TestCase):
    """V5.4.3: «Estado del sistema» en verde solo si el antivirus detecta de verdad el archivo de prueba EICAR."""

    def status(self, code):
        from helpers import Server
        tmp = Path(tempfile.mkdtemp()); f = tmp / 'av.py'; f.write_text(code)
        srv = Server({'WOD_AV_COMMAND': f'{sys.executable} {f}'}).start()

        class Caso(ServerTestCase):
            server = srv
        try:
            admin = Caso('run').make_admin('av@worldives.test', 'adminav')
            return {r['key']: r for r in admin.get('/api/admin/health').json['services']}['antivirus']
        finally:
            srv.stop(); shutil.rmtree(tmp, ignore_errors=True)

    def test_green_only_when_the_test_file_is_caught(self):
        detects = 'import sys\nd=sys.stdin.buffer.read()\nsys.exit(1 if b"EICAR-STANDARD-ANTIVIRUS-TEST-FILE" in d else 0)\n'
        row = self.status(detects)
        self.assertEqual(row['state'], 'ok', row); self.assertIn('EICAR', row['detail'])
        row = self.status('import sys\nsys.stdin.buffer.read()\nsys.exit(0)\n')         # answers, but catches nothing
        self.assertEqual(row['state'], 'error', row)
        row = self.status('import sys\nsys.exit(2)\n')                                       # clamd stopped
        self.assertEqual(row['state'], 'error', row)

    def test_the_source_never_carries_the_test_file(self):
        for p in (ROOT / 'app' / 'server.py', ROOT / 'scripts' / 'despliegue' / 'comprobar_lanzamiento.py'):
            self.assertNotIn('EICAR-STANDARD', p.read_text(encoding='utf-8'), p)

    def test_real_clamd_when_available(self):
        if not shutil.which('clamdscan') or not Path('/var/run/clamav/clamd.ctl').exists(): self.skipTest('clamd no está en marcha aquí')
        import base64
        sample = base64.b64decode(checker().EICAR)[::-1]
        r = subprocess.run(['clamdscan', '--no-summary', '--fdpass', '-'], input=sample, capture_output=True)
        self.assertEqual(r.returncode, 1, r.stdout)
        r = subprocess.run(['clamdscan', '--no-summary', '--fdpass', '-'], input=b'documento limpio', capture_output=True)
        self.assertEqual(r.returncode, 0, r.stdout)


class RegistrosExternos(ServerTestCase):
    """V16.4.2/V16.4.3: lo que lee Vector para Better Stack: sucesos de seguridad e inicios fallidos, sin datos personales."""

    def test_failed_sign_in_and_security_lines(self):
        d = self.make_diver('registro52')
        r = self.client().post('/api/auth/login', {'login': 'diver_registro52', 'password': 'Contraseña-Equivocada-99'})
        self.assertEqual(r.status, 401)
        self.client().post('/api/auth/login', {'login': 'nadie-existe@ejemplo.org', 'password': 'otra-mala-clave-1'})
        self.assertIn(d.get('/api/admin/health').status, (401, 403))             # access denied (a diver in the administration)
        time.sleep(0.5)
        log = (self.server.tmp / 'stderr.log').read_text(encoding='utf-8', errors='replace')
        self.assertRegex(log, r'\[evento\] login_failed \{"usuario": %d, "ip": "[0-9a-f]+"\}' % d.user['id'])
        self.assertRegex(log, r'\[evento\] login_failed \{"usuario": null, "ip": "[0-9a-f]+"\}')
        self.assertRegex(log, r'\[seguridad\] access_denied \{[^\n]*"usuario": %d' % d.user['id'])
        for secret in ('Contraseña-Equivocada-99', 'otra-mala-clave-1', 'nadie-existe@ejemplo.org', 'registro52@diver.example.org'):
            self.assertNotIn(secret, log)

    def test_vector_config(self):
        v = (DESPLIEGUE / 'vector.yaml').read_text(encoding='utf-8')
        self.assertIn('token: "${BETTERSTACK_TOKEN}"', v); self.assertIn('uri: "https://${BETTERSTACK_HOST}"', v)
        self.assertIn('include_units: [worldives.service]', v); self.assertIn('/var/log/caddy/worldives.log', v)
        self.assertIn('(?P<canal>seguridad|evento)', v)            # only security events: never traces or e-mails
        vector = shutil.which('vector')
        if not vector: self.skipTest('vector no está instalado aquí')
        r = subprocess.run([vector, 'validate', '--no-environment', str(DESPLIEGUE / 'vector.yaml')], capture_output=True, text=True,
                           env={**os.environ, 'BETTERSTACK_TOKEN': 'x', 'BETTERSTACK_HOST': 'ejemplo.invalid'})
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == '__main__':
    unittest.main()
