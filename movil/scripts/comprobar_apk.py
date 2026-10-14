"""Checks the two APKs (encargo «App móvil en 3 módulos», 9.3 and 11.11): the production one (com.worldives.app) carries
no test accounts, no server setting and no plain HTTP; the test one (com.worldives.app.pruebas) does, so the check
itself is proven to work. Usage: python3 comprobar_apk.py <produccion.apk> <pruebas.apk>. Exit 1 on any problem."""
import json
import sys
import zipfile

CUENTAS = [b'buzo.prueba', b'centro.prueba', b'centro2.prueba', b'freelance.prueba', b'admin.prueba', b'Worldives-Prueba-2026']
RASTROS = {'cuentas de prueba': CUENTAS, 'ajuste de servidor': [b'ServidorPlugin', b'Servidor de pruebas'], 'HTTP sin cifrar': [b'usesCleartextTraffic']}


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
    if srv.get('url') != 'https://worlddivesdiscovery.com': problems.append(f'producción: server.url debe ser https://worlddivesdiscovery.com, es {srv.get("url")!r}')
    if srv.get('cleartext') or cp.get('android', {}).get('allowMixedContent') or cp.get('android', {}).get('webContentsDebuggingEnabled'):
        problems.append('producción: HTTP sin cifrar, contenido mixto o depuración activados')
    # the test APK must have them (otherwise the check above proves nothing)
    for que, n in (('cuentas de prueba', b'buzo.prueba'), ('ajuste de servidor', b'ServidorPlugin'), ('HTTP sin cifrar', b'usesCleartextTraffic')):
        if not busca(t, n): problems.append(f'pruebas: debería llevar {que} ({n.decode()}) y no lo lleva')
    if ct.get('appId') != 'com.worldives.app.pruebas': problems.append(f'pruebas: appId {ct.get("appId")!r}')
    for x in problems: print('  ✗', x)
    print(f'Comprobación de las APK: {"correcta" if not problems else str(len(problems)) + " problemas"}')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1], sys.argv[2]))
