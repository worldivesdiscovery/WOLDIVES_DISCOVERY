"""Roles of the team of a centre (v50.49, Tanda 2 de la app).

Each centre names its own roles («Instructor máster», «Encargado de tienda»…) and chooses what each one can do from a
short list of permissions. The web edits them (Panel → Equipo); the app reads the permissions of the person signed in
through /api/me and shows only what that person can use. The server is the one that decides (team_gate).

Fixed rules:
- the owner can do everything; what only the owner can do never goes into a role (SOLO_PROPIETARIO);
- the four roles of before keep their key; until the centre changes them: the manager can do everything except what
  only the owner can do (owner's decision, 13/10), reception what it could do before (without mass notices, as the
  notices brief of v50.47 says) and the instructor the check-in of the boat;
- a role the centre created is stored as 'r' + 8 hex characters in center_members.member_role;
- a key that is neither a built-in role nor a role of that centre has no permissions (read only): an unknown value is
  never «owner».
"""
import json
import re
import secrets

# (key, name, what it allows). Order = order on screen.
PERMISOS = (
    ('checkin', 'Pasar lista y escanear QR', 'Marca quién ha llegado, escanea los QR de las reservas, recoge las firmas a bordo y cuenta a bordo.'),
    ('todas_salidas', 'Ver todas las salidas', 'Sin este permiso solo ve las salidas en las que guía un grupo y las que aún no tienen guías.'),
    ('barco', 'Organizar barcos y grupos', 'Barcos, grupos y guías de cada salida.'),
    ('reservas', 'Reservas, solicitudes y clientes', 'Acepta o rechaza solicitudes, crea y cambia reservas, cobra en el centro y escribe a los clientes.'),
    ('salidas', 'Salidas y servicios', 'Crea, cambia y cierra salidas y servicios.'),
    ('avisos', 'Cancelar salidas y avisar a todos', 'Cancela o cambia una salida y envía el aviso a todos sus buceadores.'),
    ('cobros', 'Cobros y devoluciones', 'Ve los cobros, exporta los pagos y devuelve dinero. Si el centro cobra online, pide la verificación en dos pasos.'),
    ('centro', 'Ficha del centro y ajustes', 'Ficha pública, fotos, tarifas, seguro, política de cancelación, descargo, integraciones e importar clientes.'),
    ('estadisticas', 'Estadísticas', 'Ve las estadísticas del centro.'),
)
CLAVES = tuple(k for k, _, _ in PERMISOS)
SOLO_PROPIETARIO = ('El equipo y sus perfiles', 'La cuenta de Stripe y los datos de cobro', 'Los datos fiscales', 'El plan',
                    'El registro de actividad', 'Cerrar la cuenta del centro')

BASE = {'owner': 'Propietario', 'manager': 'Encargado', 'reception': 'Recepción', 'instructor': 'Instructor'}
POR_DEFECTO = {
    # «Encargado: todo lo demás» (decisión del titular, 13/10): everything except what only the owner can do.
    'manager': CLAVES,
    'reception': ('checkin', 'todas_salidas', 'barco', 'reservas', 'salidas', 'estadisticas'),
    'instructor': ('checkin',),
}
CLAVE_PROPIA = re.compile(r'r[0-9a-f]{8}')
MAX_ROLES = 20

SCHEMA = '''CREATE TABLE IF NOT EXISTS center_roles (center_id INTEGER NOT NULL REFERENCES centers(id) ON DELETE CASCADE, role_key TEXT NOT NULL,
  name TEXT, permissions TEXT NOT NULL DEFAULT '[]', created_at TEXT NOT NULL, updated_at TEXT NOT NULL, updated_by INTEGER,
  PRIMARY KEY(center_id, role_key))'''


def limpiar(perms):
    """Only known permissions, in the order of the list, without repetitions."""
    have = {str(p) for p in (perms or [])}
    return [k for k in CLAVES if k in have]


def _fila(db, center_id, key):
    return db.execute('SELECT role_key,name,permissions FROM center_roles WHERE center_id=? AND role_key=?', (int(center_id), key)).fetchone()


def permisos(db, center_id, key):
    """Permissions of a role key in a centre (frozenset). The owner has all."""
    if key == 'owner': return frozenset(CLAVES)
    if not center_id or not key: return frozenset()
    r = _fila(db, center_id, key)
    if r: return frozenset(limpiar(json.loads(r['permissions'] or '[]')))
    return frozenset(POR_DEFECTO.get(key, ()))


def existe(db, center_id, key):
    return key in BASE or bool(CLAVE_PROPIA.fullmatch(key or '') and _fila(db, center_id, key))


def nombre(db, center_id, key):
    if key in BASE: return BASE[key]
    r = _fila(db, center_id, key) if center_id and key else None
    return (r['name'] if r and r['name'] else 'Perfil sin nombre')


def lista(db, center_id):
    """Every role of the centre: the four built-in ones (with the permissions the centre gave them) and its own."""
    cid = int(center_id)
    uso = {r['member_role']: r['n'] for r in db.execute('SELECT member_role,COUNT(*) n FROM center_members WHERE center_id=? GROUP BY member_role', (cid,))}
    inv = {r['member_role']: r['n'] for r in db.execute('SELECT member_role,COUNT(*) n FROM team_invites WHERE center_id=? AND used_at IS NULL AND revoked_at IS NULL GROUP BY member_role', (cid,))}
    out = []
    for key, label in BASE.items():
        r = _fila(db, cid, key) if key != 'owner' else None
        out.append({'key': key, 'name': label, 'builtin': True, 'permissions': sorted(permisos(db, cid, key), key=CLAVES.index),
                    'changed': bool(r), 'members': uso.get(key, 0), 'invites': inv.get(key, 0), 'owner': key == 'owner'})
    for r in db.execute("SELECT role_key,name,permissions FROM center_roles WHERE center_id=? AND role_key LIKE 'r%' ORDER BY name COLLATE NOCASE", (cid,)):
        out.append({'key': r['role_key'], 'name': r['name'] or 'Perfil sin nombre', 'builtin': False, 'permissions': limpiar(json.loads(r['permissions'] or '[]')),
                    'changed': True, 'members': uso.get(r['role_key'], 0), 'invites': inv.get(r['role_key'], 0), 'owner': False})
    return out


def guardar(db, center_id, data, user_id, ahora):
    """Creates a role (no key) or changes one. Built-in roles change only their permissions; «reset» gives them back
    the ones of before. The owner role does not change. Returns the key."""
    cid = int(center_id); key = str(data.get('key') or '').strip()
    perms = limpiar(data.get('permissions'))
    if key == 'owner': raise ValueError('El propietario siempre puede hacerlo todo: su perfil no se cambia.')
    if key in BASE:
        if data.get('reset'):
            db.execute('DELETE FROM center_roles WHERE center_id=? AND role_key=?', (cid, key)); return key
        db.execute('''INSERT INTO center_roles(center_id,role_key,name,permissions,created_at,updated_at,updated_by) VALUES(?,?,NULL,?,?,?,?)
                      ON CONFLICT(center_id,role_key) DO UPDATE SET permissions=excluded.permissions,updated_at=excluded.updated_at,updated_by=excluded.updated_by''',
                   (cid, key, json.dumps(perms), ahora, ahora, user_id))
        return key
    name = re.sub(r'\s+', ' ', str(data.get('name') or '')).strip()[:40]
    if not name: raise ValueError('Ponle un nombre al perfil (por ejemplo, «Instructor máster»).')
    taken = {x['name'].casefold(): x['key'] for x in lista(db, cid)}
    if taken.get(name.casefold(), key) != key: raise ValueError('Ya hay un perfil con ese nombre.')
    if key:
        if not CLAVE_PROPIA.fullmatch(key) or not _fila(db, cid, key): raise ValueError('Ese perfil no existe.')
        db.execute('UPDATE center_roles SET name=?,permissions=?,updated_at=?,updated_by=? WHERE center_id=? AND role_key=?', (name, json.dumps(perms), ahora, user_id, cid, key))
        return key
    if db.execute("SELECT COUNT(*) FROM center_roles WHERE center_id=? AND role_key LIKE 'r%'", (cid,)).fetchone()[0] >= MAX_ROLES:
        raise ValueError(f'Como máximo {MAX_ROLES} perfiles propios por centro.')
    key = 'r' + secrets.token_hex(4)
    db.execute('INSERT INTO center_roles(center_id,role_key,name,permissions,created_at,updated_at,updated_by) VALUES(?,?,?,?,?,?,?)',
               (cid, key, name, json.dumps(perms), ahora, ahora, user_id))
    return key


def borrar(db, center_id, key):
    """Deletes a role the centre created, only if nobody has it (people or pending invitations)."""
    cid = int(center_id)
    if key in BASE: raise ValueError('Los perfiles de siempre no se borran; puedes cambiar lo que pueden hacer.')
    if not CLAVE_PROPIA.fullmatch(key or '') or not _fila(db, cid, key): raise ValueError('Ese perfil no existe.')
    n = db.execute('SELECT COUNT(*) FROM center_members WHERE center_id=? AND member_role=?', (cid, key)).fetchone()[0]
    i = db.execute('SELECT COUNT(*) FROM team_invites WHERE center_id=? AND member_role=? AND used_at IS NULL AND revoked_at IS NULL', (cid, key)).fetchone()[0]
    if n or i: raise ValueError(f'Antes cambia el perfil de las {n + i} personas o invitaciones que lo tienen.' if n + i > 1 else 'Antes cambia el perfil de la persona o invitación que lo tiene.')
    db.execute('DELETE FROM center_roles WHERE center_id=? AND role_key=?', (cid, key))


def catalogo():
    return {'permissions': [{'key': k, 'name': n, 'help': h} for k, n, h in PERMISOS], 'owner_only': list(SOLO_PROPIETARIO)}


# ------------------------------------------------------------------------------------------------- what needs what
# POST paths. First match wins. None = only the owner. '' = everyone in the team (their own account, legal, reports).
_P = lambda *a: tuple(a)
REGLAS_POST = (
    (None, _P('/api/payments/connect/', '/api/provider/payment-profile', '/api/provider/fiscal', '/api/provider/plan', '/api/center/team',
              '/api/provider/cuenta/')),
    ('', _P('/api/auth/', '/api/account/', '/api/legal/accept', '/api/reports', '/api/contact', '/api/me', '/api/team/', '/api/app/push/',
            '/api/logbook', '/api/buddies')),   # v50.57: each person's own logbook and buddies
    # v50.57: the dives of the centre and their QR for the divers' logbooks (whoever runs the dive), the passport's logo
    ('checkin', _P('/api/center/logbook/dive')),
    ('centro', _P('/api/center/logbook/settings', '/api/center/logbook/logo')),
    ('checkin', _P('/api/manifest/sync', '/api/pro/escanear', '/api/pro/contar', re.compile(r'/api/bookings/\d+/waiver/sign'))),
    ('avisos', _P('/api/provider-services/slot-cancel', '/api/avisos/', '/api/whatsapp/')),
    ('barco', _P('/api/manifest/')),
    ('cobros', _P('/api/bookings/refund', re.compile(r'/api/bookings/\d+/refund'))),
    ('centro', _P('/api/provider/insurance', '/api/provider/cancellation-policy', '/api/center/cancellation-policy', '/api/center/profile',
                  '/api/provider/profile', '/api/provider/avatar', '/api/provider/center-update', '/api/provider/center-showcase',
                  '/api/provider/center-cover', '/api/provider/center-gallery', '/api/center/integration', '/api/provider/ical', '/api/center/import',
                  '/api/center/tariffs', '/api/provider/waiver', '/api/marina/',
                  # v50.56 · «Vender en tu web»: widget, page, API keys, webhooks and imported calendars
                  '/api/provider/vender', '/api/provider/api-keys', '/api/provider/webhooks', '/api/provider/ical-imports')),
    ('salidas', _P('/api/provider/spot-blocks',)),   # v50.56: spots kept for a group, agency or hotel
    ('salidas', _P('/api/provider-services', '/api/service-templates/', '/api/agenda/')),
)
REGLAS_GET = (
    (None, _P('/api/provider/fiscal', '/api/provider/plan', '/api/center/team', '/api/center/activity', '/api/provider/cuenta')),
    ('cobros', _P('/api/provider/payments', '/api/payments/center')),
    # ASVS 5.0 V8.2.1: requests, clients and their contact details (the exports are checked by kind in the route).
    ('reservas', _P('/api/center/requests', '/api/center/clients', '/api/center/info-requests', '/api/provider/feed',
                    re.compile(r'/api/center/bookings/\d+/insurance'))),   # v50.56: the insurance of the participants
    ('centro', _P('/api/provider/ical', '/api/provider/api-keys', '/api/provider/webhooks', '/api/provider/ical-imports')),
    ('estadisticas', _P('/api/provider/stats', '/api/center/analytics', '/api/provider/ventas-canal')),
)


def _coincide(path, pats):
    return any(p.fullmatch(path) if hasattr(p, 'fullmatch') else path.startswith(p) for p in pats)


def necesita(path, method):
    """The permission a request needs: None (owner only), '' (anyone of the team) or a permission key.
    Reading (GET) is free except the listed paths (and what each route filters: departures by guide, amounts and
    internal notes, exports by kind; docs/seguridad/permisos.md); writing needs «reservas» when nothing more specific
    applies."""
    reglas = REGLAS_GET if method == 'GET' else REGLAS_POST
    for perm, pats in reglas:
        if _coincide(path, pats): return perm
    return '' if method == 'GET' else 'reservas'


NO_PUEDE = {
    None: 'Solo el propietario del centro puede hacer esto.',
    'checkin': 'Tu perfil no permite pasar lista ni escanear. Pídeselo al propietario del centro.',
    'avisos': 'Tu perfil no permite cancelar salidas ni avisar a todos los clientes. Pídeselo al propietario del centro.',
    'barco': 'Tu perfil no permite organizar barcos y grupos. Pídeselo al propietario del centro.',
    'cobros': 'Tu perfil no permite ver cobros ni devolver dinero. Pídeselo al propietario del centro.',
    'centro': 'Tu perfil no permite cambiar la ficha ni los ajustes del centro. Pídeselo al propietario del centro.',
    'salidas': 'Tu perfil no permite crear ni cambiar salidas y servicios. Pídeselo al propietario del centro.',
    'estadisticas': 'Tu perfil no permite ver las estadísticas. Pídeselo al propietario del centro.',
    'reservas': 'Tu perfil es de solo lectura para esto. Pídeselo al propietario del centro.',
}
# Reading what needs «reservas» (requests, clients, their exports).
NO_VE_RESERVAS = 'Tu perfil no permite ver las solicitudes ni los clientes. Pídeselo al propietario del centro.'
