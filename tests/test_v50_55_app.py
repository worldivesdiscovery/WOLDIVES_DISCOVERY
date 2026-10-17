"""v50.55 · Encargo 2 «Seguridad de la app WORLDIVES PRO»: what can be checked without a phone.

  · Point 4, no secret key in the app: the search of movil/scripts/comprobar_apk.py finds the keys it should (a
    synthetic APK) and nothing in a clean one; the same search over everything the app is made of or opens (the
    native project, the launcher of WORLDIVES Pruebas and the web pages served to the app) gives zero results.
  · The native plugin: the device token in the Android Keystore behind the fingerprint or the phone's code, 5 failed
    attempts wipe the phone, the panel hidden in the recent apps, nothing of the app in backups or phone transfers.
  · The web side (public/js/wd-app-seg.js): only in the native app, before wd-app.js; the refresh token is handed to
    the phone and never written to the web storage; the offline data are encrypted (AES-GCM) and deleted after 7 days.
The behaviour on a real Android is checked on the emulator (movil/scripts/emulador.py) and the web side in a browser
with a test double of the plugin (tests/navegador/e2e_v50_55_seguridad_app.py)."""
import re
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'movil' / 'scripts'))
import comprobar_apk  # noqa: E402

TEXT = ('.js', '.mjs', '.html', '.css', '.json', '.xml', '.java', '.kt', '.gradle', '.properties', '.txt', '.md', '.webmanifest')
PLUGIN = (ROOT / 'movil/android/app/src/main/java/com/worldives/app/SeguridadPlugin.java').read_text(encoding='utf-8')
SEG = (ROOT / 'public/js/wd-app-seg.js').read_text(encoding='utf-8')
WEB = (ROOT / 'public/js/world-dives-v8.js').read_text(encoding='utf-8')


def fake(*parts):
    return ''.join(parts)   # built at run time, so this file never carries something that looks like a real key


class SinClavesEnLaApp(unittest.TestCase):
    def apk(self, files):
        p = Path(tempfile.mkdtemp(prefix='wod-apk-')) / 'x.apk'
        with zipfile.ZipFile(p, 'w') as z:
            for n, data in files.items(): z.writestr(n, data)
        return p

    def test_the_search_finds_what_it_must(self):
        bad = self.apk({
            'classes.dex': b'\x00\x01' + fake('sk_', 'live_', 'A1b2C3d4E5f6G7h8I9j0K1').encode(),
            'assets/public/config.js': fake('const k="AI', 'za', 'B' * 35, '";').encode(),
            'res/xml/x.xml': fake('wh', 'sec_', 'abcdefghij1234').encode('utf-16-le'),        # binary XML: UTF-16
            'assets/a.txt': fake('-----BEGIN ', 'PRIVATE KEY-----').encode(),
            'assets/env.txt': fake('STRIPE_SECRET', '_KEY=', 'abcdefgh12345').encode(),
            'assets/firma.jks': b'\xfe\xed\xfe\xed',
        })
        found = {que for que, _ in comprobar_apk.secretos(bad)}
        for que in ('clave secreta de Stripe', 'clave de API de Google', 'secreto de webhook de Stripe', 'clave privada',
                    'secreto del .env del servidor', 'almacén de claves o .env dentro de la app'):
            self.assertIn(que, found)
        clean = self.apk({'classes.dex': b'pk_live_public_key_is_not_secret sk_ noop', 'assets/public/index.html': b'<p>WORLDIVES</p>'})
        self.assertEqual(comprobar_apk.secretos(clean), [])

    def test_nothing_the_app_is_made_of_or_opens_has_a_secret(self):
        roots = [ROOT / 'movil' / 'android' / 'app' / 'src', ROOT / 'movil' / 'www', ROOT / 'public',
                 ROOT / 'movil' / 'capacitor.config.json', ROOT / 'movil' / 'android' / 'app' / 'build.gradle']
        files = []
        for r in roots:
            files += [r] if r.is_file() else [f for f in r.rglob('*') if f.is_file() and f.suffix.lower() in TEXT]
        self.assertGreater(len(files), 50)
        hits = []
        for f in files:
            data = f.read_bytes()
            hits += [(que, str(f.relative_to(ROOT))) for que, rx in comprobar_apk.SECRETOS.items() if re.search(rx, data)]
            if f.suffix.lower() in comprobar_apk.ALMACENES: hits.append(('almacén de claves', str(f)))
        self.assertEqual(hits, [], 'claves secretas en la app o en lo que abre')

    def test_the_build_checks_both_apks(self):
        wf = (ROOT / '.github/workflows/app-android.yml').read_text(encoding='utf-8')
        self.assertIn('comprobar_apk.py', wf)
        for path in ('public/js/wd-app-seg.js', 'public/js/wd-app-pro.js', 'public/js/world-dives-v8.js', 'app/wod/dispositivos.py'):
            self.assertIn(f"'{path}'", wf, f'el APK se vuelve a compilar y probar cuando cambia {path}')


class PluginNativo(unittest.TestCase):
    def test_token_behind_the_fingerprint_or_the_phone_code(self):
        self.assertIn('@CapacitorPlugin(name = "Seguridad")', PLUGIN)
        self.assertIn('setUserAuthenticationRequired(true)', PLUGIN)
        self.assertIn('KeyProperties.AUTH_BIOMETRIC_STRONG | KeyProperties.AUTH_DEVICE_CREDENTIAL', PLUGIN)
        self.assertIn('"AndroidKeyStore"', PLUGIN)
        self.assertIn('AES/GCM/NoPadding', PLUGIN)
        self.assertRegex(PLUGIN, r'MAX_FALLOS = 5;')
        self.assertIn('PBKDF2WithHmacSHA256', PLUGIN)       # the app's PIN, when the phone has no screen lock
        self.assertIn('KeyPermanentlyInvalidatedException', PLUGIN)   # fingerprints changed: the session ends
        self.assertNotRegex(PLUGIN, r'\bLog\.[dviwe]\(')     # nothing written to the phone's log
        self.assertNotIn('call.getLong(', PLUGIN)              # it gives the default for small numbers (they arrive as Integer)
        self.assertIn('setRecentsScreenshotEnabled', PLUGIN); self.assertIn('FLAG_SECURE', PLUGIN)
        self.assertIn('WebStorage.getInstance().deleteAllData()', PLUGIN); self.assertIn('removeAllCookies', PLUGIN)

    def test_wired_in_both_variants(self):
        for v in ('produccion', 'pruebas'):
            src = (ROOT / f'movil/android/app/src/{v}/java/com/worldives/app/MainActivity.java').read_text(encoding='utf-8')
            self.assertIn('registerPlugin(SeguridadPlugin.class)', src, v)
        gradle = (ROOT / 'movil/android/app/build.gradle').read_text(encoding='utf-8')
        self.assertIn('androidx.biometric:biometric:', gradle)
        man = (ROOT / 'movil/android/app/src/main/AndroidManifest.xml').read_text(encoding='utf-8')
        self.assertIn('android.permission.USE_BIOMETRIC', man)
        self.assertIn('android:allowBackup="false"', man); self.assertIn('android:dataExtractionRules="@xml/reglas_datos"', man)
        rules = (ROOT / 'movil/android/app/src/main/res/xml/reglas_datos.xml').read_text(encoding='utf-8')
        for part in ('cloud-backup', 'device-transfer'):
            block = rules.split(f'<{part}>')[1].split(f'</{part}>')[0]
            for domain in ('root', 'file', 'database', 'sharedpref'):
                self.assertIn(f'<exclude domain="{domain}"', block, (part, domain))


class LadoWeb(unittest.TestCase):
    def test_only_in_the_native_app_and_before_wd_app(self):
        self.assertIn("if (!W || !W.app || !W.app.native) return;", SEG)
        self.assertIn("(WD_APP.native?script('/js/wd-app-seg.js'):Promise.resolve()).then(()=>script('/js/wd-app.js'))", WEB)
        self.assertIn("await window.WD_SEC?.inicio?.()", WEB)                     # the lock before /api/me
        sw = (ROOT / 'public/sw.js').read_text(encoding='utf-8')
        self.assertIn("'/js/wd-app-seg.js?v=", sw)                              # also when the app opens without coverage
        self.assertIn("(r.status===401||d?.login_required) && !retried && WD_APP?.native", WEB)

    def test_refresh_token_is_never_stored_in_the_web(self):
        uses = [m.start() for m in re.finditer(r'refresh_token', SEG)]
        self.assertTrue(uses)
        for i in uses:
            line = SEG[SEG.rfind('\n', 0, i) + 1:SEG.find('\n', i)]
            self.assertTrue('S.activar(' in line or 'if (!r?.refresh_token)' in line or line.strip().startswith(('/*', '*', '//', '-')) or 'token' in line and 'Storage' not in line, line)
            self.assertNotIn('setItem', line)
        self.assertNotRegex(SEG, r'setItem\([^)]*refresh')

    def test_offline_data_encrypted_and_kept_7_days(self):
        self.assertIn("const PROTEGIDAS = /^(wd-day-|wd-sync-queue$|wda-pro-|wda-res:|wda-qr-|wda-push$)/;", SEG)
        # the phone encrypts them (the web over plain http in Pruebas has no WebCrypto, and the key never reaches it)
        self.assertNotIn('crypto.subtle', SEG)
        self.assertIn('await S.datosGuardar({ items })', SEG); self.assertIn('await S.datosLeer()', SEG)
        self.assertIn('const SIETE_DIAS = 7 * 86400e3;', SEG)
        for part in ('public void datosLeer(', 'public void datosGuardar(', 'ALIAS_DATOS', 'if (bloqueada()) { call.reject("bloqueado"); return; }'):
            self.assertIn(part, PLUGIN)
        self.assertNotIn('datosClave', PLUGIN)                                  # the key is never handed to the web
        # every key the offline code uses is one of the protected ones
        for key in ("'wd-day-'", "'wd-sync-queue'"): self.assertIn(key, WEB)
        for f in ('public/js/wd-app.js', 'public/js/wd-app-pro.js'):
            src = (ROOT / f).read_text(encoding='utf-8')
            for k in re.findall(r"localStorage\.(?:getItem|setItem)\('([^']+)'", src):
                if k.startswith(('wda-res', 'wda-qr', 'wda-pro', 'wda-push')):
                    self.assertRegex(k, r'^(wda-pro-|wda-res:|wda-qr-|wda-push$)', (f, k))

    def test_lock_threshold_is_five_minutes_and_only_tests_change_it(self):
        self.assertIn('const UMBRAL = 300;', SEG)
        self.assertIn("if (APP.pruebas) { try { const v = Number(localStorage.getItem('wda-seg-umbral'))", SEG)
        self.assertIn('const RENUEVA_MS = 12 * 60e3;', SEG)            # before the 15-minute access session ends

    def test_professionals_always_locked(self):
        self.assertIn("const PRO = (role) => ['center', 'freelance', 'admin'].includes(role);", SEG)
        self.assertIn("if (PRO(r.role) || quiereBloqueo) modo = st.seguro ? 'sistema' : 'pin';", SEG)

    def test_departure_reminder_never_asks_for_exact_alarms(self):
        # Capacitor's LocalNotifications schedules exact alarms by default and, on Android 12+ without that permission
        # (Android 14 denies it to new installs), opens the «Alarms & reminders» settings in the middle of «Hoy»
        # (seen on the emulator). A reminder 45 minutes before a departure does not need to be exact.
        pro = (ROOT / 'public/js/wd-app-pro.js').read_text(encoding='utf-8')
        calls = re.findall(r'\.schedule\(\{ notifications: \[(.*?)\] \}\)', pro, re.S)
        self.assertTrue(calls)
        for c in calls: self.assertIn('isExactNotification: false', c)


if __name__ == '__main__':
    unittest.main(verbosity=2)
