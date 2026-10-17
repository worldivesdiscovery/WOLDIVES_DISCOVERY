"""Checks the two APKs (encargo «App móvil en 3 módulos», 9.3 and 11.11): the production one (com.worldives.app) carries
no test accounts, no server setting and no plain HTTP; the test one (com.worldives.app.pruebas) does, so the check
itself is proven to work. Usage: python3 comprobar_apk.py <produccion.apk> <pruebas.apk>. Exit 1 on any problem.

v50.55 (encargo 2, punto 4 «ninguna clave secreta en la app»): every file of both APKs (code, resources, assets,
native libraries, images) is searched for secret keys and tokens; the expected result is zero. The web pages the app
opens come from the server and are searched by tests/test_v50_55_app.py with the same patterns."""
import json
import re
import sys
import zipfile

CUENTAS = [b'buzo.prueba', b'centro.prueba', b'centro2.prueba', b'freelance.prueba', b'admin.prueba', b'Worldives-Prueba-2026']
RASTROS = {'cuentas de prueba': CUENTAS, 'ajuste de servidor': [b'ServidorPlugin', b'Servidor de pruebas'], 'HTTP sin cifrar': [b'usesCleartextTraffic']}


# What a secret looks like (the public Stripe key «pk_…» and the Firebase app configuration are not secrets).
SECRETOS = {
    'clave secreta de Stripe': rb'\b(?:sk|rk)_(?:live|test)_[0-9A-Za-z]{10,}',
    'secreto de webhook de Stripe': rb'\bwhsec_[0-9A-Za-z]{10,}',
    'clave de API de Google': rb'AIza[0-9A-Za-z_\-]{35}',
    'clave de servidor de Firebase': rb'AAAA[A-Za-z0-9_\-]{7}:[A-Za-z0-9_\-]{100,}',
    'clave de ArcGIS': rb'\bAAP[KT][A-Za-z0-9_\-]{40,}',
    'clave de AWS': rb'\bAKIA[0-9A-Z]{16}\b',
    'token de GitHub': rb'\bgh[pousr]_[A-Za-z0-9]{36}\b',
    'token de Slack': rb'\bxox[baprs]-[0-9A-Za-z\-]{10,}',
    'clave privada': rb'-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----',
    'secreto del .env del servidor': rb'\b(?:STRIPE_SECRET_KEY|STRIPE_WEBHOOK_SECRET|WOD_DATA_KEY|WOD_SECRET_KEY|WOD_HMAC_KEY|ARCGIS_API_KEY|BETTERSTACK_[A-Z_]+|LOGTAIL_[A-Z_]+|SMTP_PASSWORD|WHATSAPP_[A-Z_]*TOKEN|FIREBASE_[A-Z_]*KEY)(?:\s*=\s*["\x27]?|["\x27]?\s*:\s*["\x27])[A-Za-z0-9_\-/+]{8,}',   # NAME=value or "NAME": "value", not a sentence naming it
    'contraseña de la firma': rb'(?:storePassword|keyPassword)\s*[=:]\s*["\x27][^"\x27$]{4,}',
}
ALMACENES = ('.jks', '.keystore', '.p12', '.pfx', '.pem', '.key', '.env')


def secretos(apk):
    """[(what, file)] for every secret found in any file of the APK (also in UTF-16, as binary XML keeps its strings)."""
    found = []
    with zipfile.ZipFile(apk) as z:
        for n in z.namelist():
            if n.lower().endswith(ALMACENES): found.append(('almacén de claves o .env dentro de la app', n)); continue
            data = z.read(n)
            for text in (data, data.replace(b'\x00', b'')):
                for que, rx in SECRETOS.items():
                    if re.search(rx, text) and (que, n) not in found: found.append((que, n))
    return found


def contenido(apk):
    with zipfile.ZipFile(apk) as z:
        return {n: z.read(n) for n in z.namelist() if n.endswith(('.dex', '.xml', '.json', '.html', '.js', '.css'))}


def busca(files, needle):
    variants = {needle, needle.decode('latin-1').encode('utf-16-le')}   # binary XML keeps its strings in UTF-16
    return sorted(n for n, data in files.items() if any(v in data for v in variants))


def config(files):
    return json.loads(files.get('assets/capacitor.config.json', b'{}'))


def main(prod, test):
    problems = []
    p, t = contenido(prod), contenido(test)
    for que, needles in RASTROS.items():
        for n in needles:
            if busca(p, n): problems.append(f'producción: {que} ({n.decode()}) en {", ".join(busca(p, n))}')
    cp, ct = config(p), config(t)
    srv = cp.get('server', {})
    if srv.get('url') != 'https://worldivesdiscovery.com': problems.append(f'producción: server.url debe ser https://worldivesdiscovery.com, es {srv.get("url")!r}')
    if srv.get('cleartext') or cp.get('android', {}).get('allowMixedContent') or cp.get('android', {}).get('webContentsDebuggingEnabled'):
        problems.append('producción: HTTP sin cifrar, contenido mixto o depuración activados')
    # the test APK must have them (otherwise the check above proves nothing)
    for que, n in (('cuentas de prueba', b'buzo.prueba'), ('ajuste de servidor', b'ServidorPlugin'), ('HTTP sin cifrar', b'usesCleartextTraffic')):
        if not busca(t, n): problems.append(f'pruebas: debería llevar {que} ({n.decode()}) y no lo lleva')
    if ct.get('appId') != 'com.worldives.app.pruebas': problems.append(f'pruebas: appId {ct.get("appId")!r}')
    for apk, nombre in ((prod, 'producción'), (test, 'pruebas')):
        with zipfile.ZipFile(apk) as z: total = len(z.namelist())
        hallados = secretos(apk)
        print(f'  Búsqueda de claves secretas en la APK de {nombre}: {total} archivos, {len(SECRETOS)} tipos de clave · {len(hallados)} resultados')
        problems += [f'{nombre}: {que} en {n}' for que, n in hallados]
    for x in problems: print('  ✗', x)
    print(f'Comprobación de las APK: {"correcta" if not problems else str(len(problems)) + " problemas"}')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1], sys.argv[2]))
