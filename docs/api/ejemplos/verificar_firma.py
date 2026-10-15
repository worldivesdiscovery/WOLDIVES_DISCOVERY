"""Comprobar la firma de un aviso de WORLDIVES (Python 3, sin librerías).

    ok = verificar(secreto, request.headers['X-WORLDIVES-Signature'], cuerpo_en_bruto)
"""
import hashlib
import hmac
import time

TOLERANCIA = 300   # segundos


def verificar(secreto: str, cabecera: str, cuerpo: bytes, ahora: int | None = None) -> bool:
    try:
        partes = dict(p.split('=', 1) for p in cabecera.split(','))
        t, firma = int(partes['t']), partes['v1']
    except (ValueError, KeyError):
        return False
    if abs((ahora if ahora is not None else int(time.time())) - t) > TOLERANCIA:
        return False
    esperada = hmac.new(secreto.encode(), f'{t}.'.encode() + cuerpo, hashlib.sha256).hexdigest()
    return hmac.compare_digest(esperada, firma)


# Con Flask:
#
# @app.post('/worldives/avisos')
# def avisos():
#     cuerpo = request.get_data()            # en bruto, antes de leer el JSON
#     if not verificar(os.environ['WORLDIVES_WEBHOOK_SECRET'], request.headers.get('X-WORLDIVES-Signature', ''), cuerpo):
#         return '', 400
#     aviso = json.loads(cuerpo)
#     ...                                    # guarda aviso['id'] para no procesarlo dos veces
#     return '', 204
