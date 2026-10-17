"""One door to the private data of each centre (v50.47, encargo «avisos y aislamiento», parte B).

Many diving centres and freelance professionals share WORLDIVES. Each one is a tenant («inquilino»): a centre
(centers.id) or a freelance professional without a centre (users.id). Its private data — bookings and clients, phones,
payments and refunds, settings, staff, WhatsApp, notices — can only be read or changed through the functions of this
module, which ALWAYS filter by the tenant of the session:

- The tenant comes from the session (ctx_from_user), never from the browser. A centre_id, provider_id, user_id or
  phone sent by the browser is ignored (and logged by the caller).
- An object of another tenant does not exist: NotFound → 404, exactly as an id that does not exist, so nobody can
  learn which ids exist.
- Before sending anything, same_tenant() checks again that every object involved belongs to the same tenant; if one
  does not, nothing is sent («fail closed»).

Public data (map, directory, public page of a centre, its services, departures, spots, prices, experiences and
reviews) is NOT private and is read elsewhere: this module only guards what belongs to the panel of each centre.
"""
from __future__ import annotations

from dataclasses import dataclass, field

try:
    from . import roles as wroles
except ImportError:   # loaded as a top-level module (tests of the module alone)
    import roles as wroles


class NotFound(LookupError):
    """Something asked for does not exist, is not public or belongs to another centre: 404."""


# Roles inside a centre. v50.49: each centre can add its own roles and change what each one can do (wod.roles);
# cancelling departures and sending mass notices needs the permission «avisos» (by default, owner and manager).
TEAM_ROLES = dict(wroles.BASE)
NOTICE_ROLES = ('owner', 'manager')
# Booking states that still involve the diver (recipients of a notice of a departure)
ACTIVE_STATES = ('requested', 'accepted_pending_payment', 'confirmed')


@dataclass(frozen=True)
class Ctx:
    """The verified tenant of a request. kind: 'center' or 'freelance'; oid: centers.id or users.id."""
    user_id: int
    role: str                       # users.role of the person: center, freelance or admin
    kind: str
    oid: int
    member_role: str = 'owner'      # inside a centre: owner, manager, reception, instructor or a role of the centre ('r…')
    permisos: frozenset = field(default_factory=lambda: frozenset(wroles.CLAVES), compare=False)
    admin_reason: str = ''          # only for an administrator looking at a centre's data with a stated reason
    extra: dict = field(default_factory=dict, compare=False)

    @property
    def key(self) -> str:
        """'c:12' or 'f:34': the tenant as a string (logs, cache keys, queue rows)."""
        return f"{'c' if self.kind == 'center' else 'f'}:{self.oid}"

    @property
    def can_send_notices(self) -> bool:
        return self.role in ('center', 'freelance') and (self.kind == 'freelance' or 'avisos' in self.permisos)

    def puede(self, permiso) -> bool:
        return self.kind == 'freelance' or self.member_role == 'owner' or permiso in self.permisos


def tenant_key(kind, oid) -> str:
    return f"{'c' if kind == 'center' else 'f'}:{int(oid)}"


def member_role(db, center_id, user_id) -> str:
    """The role of a person in a centre. No row: the account that created the centre (owner, as always). A value that is
    not a role any more keeps its key and has no permissions: it is never taken as «owner» (v50.49)."""
    r = db.execute('SELECT member_role FROM center_members WHERE center_id=? AND user_id=?', (center_id, user_id)).fetchone()
    return (r['member_role'] or '') if r else 'owner'


def ctx_from_user(db, user):
    """The tenant of the signed-in person, from the session only. None for divers and administrators."""
    if not user: return None
    if user['role'] == 'center' and user.get('center_id'):
        mr = member_role(db, int(user['center_id']), int(user['id']))
        return Ctx(int(user['id']), 'center', 'center', int(user['center_id']), mr, wroles.permisos(db, int(user['center_id']), mr))
    if user['role'] == 'freelance':
        # A freelance professional is always a tenant of their own (v50.47: before, a freelance «attached» to a centre
        # by the administration acted as the owner of that centre in some screens and as freelance in others).
        return Ctx(int(user['id']), 'freelance', 'freelance', int(user['id']))
    return None


def require_ctx(db, user):
    ctx = ctx_from_user(db, user)
    if not ctx: raise PermissionError('Solo los centros y profesionales tienen panel.')
    return ctx


def admin_ctx(user, kind, oid, reason) -> Ctx:
    """An administrator looks at the private data of one centre: only with a reason (logged by the caller)."""
    reason = (reason or '').strip()
    if len(reason) < 5: raise PermissionError('Indica el motivo para ver los datos de este centro (queda registrado).')
    if kind not in ('center', 'freelance'): raise NotFound('Centro no encontrado.')
    return Ctx(int(user['id']), 'admin', kind, int(oid), 'admin', admin_reason=reason[:300])


# ------------------------------------------------------------------------------------------- SQL of the tenant
def owner_filter(ctx: Ctx, alias: str = '', center_col: str = 'center_id', user_col: str = 'provider_user_id'):
    """WHERE fragment and arguments for a table with a centre column and a freelance column."""
    a = (alias + '.') if alias else ''
    if ctx.kind == 'center': return f'{a}{center_col}=?', [ctx.oid]
    return f'({a}{center_col} IS NULL AND {a}{user_col}=?)', [ctx.oid]


def get_service(db, ctx: Ctx, service_id):
    w, a = owner_filter(ctx, 's')
    row = db.execute(f'SELECT s.* FROM provider_services s WHERE s.id=? AND {w}', (int(service_id or 0), *a)).fetchone()
    if not row: raise NotFound('Servicio no encontrado.')
    return row


def get_slot(db, ctx: Ctx, slot_id):
    """A departure of the tenant, with the owner columns of its service (center_id, provider_user_id, title…)."""
    w, a = owner_filter(ctx, 's')
    row = db.execute(f'''SELECT ss.*, s.center_id, s.provider_user_id, s.title AS service_title, s.service_type, s.currency AS service_currency
                           FROM service_slots ss JOIN provider_services s ON s.id=ss.service_id WHERE ss.id=? AND {w}''', (int(slot_id or 0), *a)).fetchone()
    if not row: raise NotFound('Salida no encontrada.')
    return row


def get_booking(db, ctx: Ctx, booking_id):
    w, a = owner_filter(ctx, 'b')
    row = db.execute(f'SELECT b.* FROM bookings b WHERE b.id=? AND {w}', (int(booking_id or 0), *a)).fetchone()
    if not row: raise NotFound('Reserva no encontrada.')
    return row


def get_payment_order(db, ctx: Ctx, order_id):
    """A payment of the tenant: its payee is the tenant AND its booking (if any) is of the tenant."""
    o = db.execute('SELECT * FROM payment_orders WHERE id=?', (int(order_id or 0),)).fetchone()
    if not o or o['payee_type'] != ctx.kind or int(o['payee_id'] or 0) != ctx.oid: raise NotFound('Pago no encontrado.')
    if o['booking_id']: get_booking(db, ctx, o['booking_id'])
    return o


def slot_bookings(db, ctx: Ctx, slot_id, states=ACTIVE_STATES):
    """The bookings of one departure of the tenant (the slot is checked first). Never from a list sent by the browser."""
    slot = get_slot(db, ctx, slot_id)
    w, a = owner_filter(ctx, 'b')
    ph = ','.join('?' * len(states))
    rows = db.execute(f'''SELECT b.* FROM bookings b WHERE b.slot_id=? AND {w} AND b.status IN ({ph}) ORDER BY b.id''',
                      (slot['id'], *a, *states)).fetchall()
    return slot, rows


def booking_tenant(b):
    """(kind, oid) of a booking row."""
    return ('center', int(b['center_id'])) if b['center_id'] else ('freelance', int(b['provider_user_id'] or 0))


def slot_tenant(slot):
    """(kind, oid) of a slot row joined with its service (center_id, provider_user_id)."""
    return ('center', int(slot['center_id'])) if slot['center_id'] else ('freelance', int(slot['provider_user_id'] or 0))


def same_tenant(ctx: Ctx, *, slot=None, booking=None, account=None) -> list:
    """Every object of a send belongs to the tenant of the session. Returns the list of mismatches (empty = OK).
    account: the WhatsApp account row (kind, oid columns)."""
    bad = []
    me = (ctx.kind, ctx.oid)
    if slot is not None and slot_tenant(slot) != me: bad.append('salida')
    if booking is not None:
        if booking_tenant(booking) != me: bad.append('reserva')
        if slot is not None and booking['slot_id'] != slot['id']: bad.append('reserva de otra salida')
    if account is not None and (account['kind'], int(account['oid'])) != me: bad.append('número de WhatsApp')
    return bad


def first_name_initial(name: str) -> str:
    """«Ana García López» → «Ana G.» (lists shown before a mass notice)."""
    parts = [p for p in str(name or '').split() if p]
    if not parts: return '—'
    return parts[0] + (f' {parts[1][0]}.' if len(parts) > 1 else '')


# ------------------------------------------------------------------------------------------ schema (B.5, v50.47)
# Every table with private data of a tenant has a column provider_id ('c:<centre id>' or 'f:<user id>'), NOT NULL and
# with a foreign key to providers(id). In the tables that already say who owns each row (centre column + freelance
# column) it is a generated column: it is computed from those columns, so it can never disagree with them. Departures
# (service_slots) take it from their service through triggers. New rows without a tenant are refused by the database
# itself; rows of before v50.47 whose tenant cannot be known go to the tenant 'x:0' (quarantine): no centre ever sees them.
OWNER_TABLES = {   # table: (centre column, freelance column)
    'provider_services': ('center_id', 'provider_user_id'),
    'bookings': ('center_id', 'provider_user_id'),
    'boats': ('center_id', 'provider_user_id'),
    'waiver_templates': ('center_id', 'provider_user_id'),
    'travel_experiences': ('center_id', 'provider_user_id'),
    'info_requests': ('center_id', 'provider_user_id'),
    'resources': ('owner_center_id', 'owner_user_id'),
}
CENTER_TABLES = ('center_tariffs', 'center_extras', 'center_equipment', 'center_integrations', 'center_members', 'center_links', 'data_shares',
                 'promotions', 'qr_codes', 'team_invites')
TENANT_INDEXES = {
    'bookings': ('provider_id, status, booking_date', 'provider_id, slot_id'),
    'provider_services': ('provider_id, active',),
    'service_slots': ('provider_id, slot_date',),
    'payment_orders': ('provider_id, created_at',),
    'boats': ('provider_id',), 'waiver_templates': ('provider_id',), 'travel_experiences': ('provider_id',),
    'info_requests': ('provider_id, created_at',), 'resources': ('provider_id',),
}
_STAMP = "strftime('%Y-%m-%dT%H:%M:%SZ','now')"


def owner_expr(c, u, p=''):
    """SQL for the tenant key of a row (p='NEW.' inside triggers)."""
    return f"(CASE WHEN {p}{c} IS NOT NULL THEN 'c:'||{p}{c} WHEN {p}{u} IS NOT NULL THEN 'f:'||{p}{u} ELSE 'x:0' END)"


def _payee_expr(p=''):
    return (f"(CASE WHEN {p}payee_type='center' AND {p}payee_id IS NOT NULL THEN 'c:'||{p}payee_id "
            f"WHEN {p}payee_type='freelance' AND {p}payee_id IS NOT NULL THEN 'f:'||{p}payee_id ELSE 'x:0' END)")


def _xcols(db, table):
    return {r[1] for r in db.execute(f'PRAGMA table_xinfo("{table}")')}


def _ensure_providers(c, u, table, p):
    """Statements (inside a trigger) that create the providers row the new row will point to, if missing."""
    return (f"INSERT OR IGNORE INTO providers(id,kind,center_id,created_at) SELECT 'c:'||{p}{c},'center',{p}{c},{_STAMP} WHERE {p}{c} IS NOT NULL;\n"
            f"  INSERT OR IGNORE INTO providers(id,kind,user_id,created_at) SELECT 'f:'||{p}{u},'freelance',{p}{u},{_STAMP} WHERE {p}{c} IS NULL AND {p}{u} IS NOT NULL;")


def install_schema(db):
    """Creates (idempotently) the tenant schema. Returns a report {table: rows in quarantine}."""
    db.execute('''CREATE TABLE IF NOT EXISTS providers (id TEXT PRIMARY KEY, kind TEXT NOT NULL CHECK (kind IN ('center','freelance','quarantine')),
        center_id INTEGER UNIQUE REFERENCES centers(id), user_id INTEGER UNIQUE REFERENCES users(id), created_at TEXT NOT NULL,
        CHECK ((kind='center' AND center_id IS NOT NULL AND user_id IS NULL AND id='c:'||center_id)
            OR (kind='freelance' AND user_id IS NOT NULL AND center_id IS NULL AND id='f:'||user_id)
            OR (kind='quarantine' AND id='x:0' AND center_id IS NULL AND user_id IS NULL)))''')
    db.execute(f"INSERT OR IGNORE INTO providers(id,kind,created_at) VALUES('x:0','quarantine',{_STAMP})")
    db.execute(f"INSERT OR IGNORE INTO providers(id,kind,center_id,created_at) SELECT 'c:'||id,'center',id,{_STAMP} FROM centers")
    db.execute(f"INSERT OR IGNORE INTO providers(id,kind,user_id,created_at) SELECT 'f:'||id,'freelance',id,{_STAMP} FROM users WHERE role='freelance'")
    db.execute(f'''CREATE TRIGGER IF NOT EXISTS wod_centers_provider AFTER INSERT ON centers BEGIN
        INSERT OR IGNORE INTO providers(id,kind,center_id,created_at) VALUES('c:'||NEW.id,'center',NEW.id,{_STAMP}); END''')
    db.execute(f'''CREATE TRIGGER IF NOT EXISTS wod_users_provider AFTER UPDATE OF role ON users WHEN NEW.role='freelance' BEGIN
        INSERT OR IGNORE INTO providers(id,kind,user_id,created_at) VALUES('f:'||NEW.id,'freelance',NEW.id,{_STAMP}); END''')
    report = {}
    for t, (c, u) in OWNER_TABLES.items():
        # the providers rows of the existing data (only for centres and users that exist: orphans stay as they are)
        db.execute(f"INSERT OR IGNORE INTO providers(id,kind,center_id,created_at) SELECT DISTINCT 'c:'||t.{c},'center',t.{c},{_STAMP} FROM {t} t JOIN centers x ON x.id=t.{c}")
        db.execute(f"INSERT OR IGNORE INTO providers(id,kind,user_id,created_at) SELECT DISTINCT 'f:'||t.{u},'freelance',t.{u},{_STAMP} FROM {t} t JOIN users x ON x.id=t.{u} WHERE t.{c} IS NULL")
        if 'provider_id' not in _xcols(db, t):
            db.execute(f'ALTER TABLE {t} ADD COLUMN provider_id TEXT GENERATED ALWAYS AS {owner_expr(c, u)} VIRTUAL NOT NULL REFERENCES providers(id)')
        for when, name in (('BEFORE INSERT', 'ins'), (f'BEFORE UPDATE OF {c},{u}', 'upd')):
            db.execute(f'''CREATE TRIGGER IF NOT EXISTS wod_{t}_tenant_{name} {when} ON {t} BEGIN
              SELECT RAISE(ABORT, 'WOD: dato sin centro ({t})') WHERE NEW.{c} IS NULL AND NEW.{u} IS NULL;
              {_ensure_providers(c, u, t, 'NEW.')}
            END''')
        report[t] = db.execute(f"SELECT COUNT(*) FROM {t} WHERE provider_id='x:0'").fetchone()[0]
    for t in CENTER_TABLES:
        if 'provider_id' not in _xcols(db, t):
            db.execute(f"ALTER TABLE {t} ADD COLUMN provider_id TEXT GENERATED ALWAYS AS ('c:'||center_id) VIRTUAL NOT NULL REFERENCES providers(id)")
        db.execute(f'CREATE INDEX IF NOT EXISTS idx_{t}_provider ON {t}(provider_id)')
    # Payments: the tenant is the payee (the account that received the money).
    if 'provider_id' not in _xcols(db, 'payment_orders'):
        db.execute(f'ALTER TABLE payment_orders ADD COLUMN provider_id TEXT GENERATED ALWAYS AS {_payee_expr()} VIRTUAL NOT NULL REFERENCES providers(id)')
    report['payment_orders'] = db.execute("SELECT COUNT(*) FROM payment_orders WHERE provider_id='x:0'").fetchone()[0]
    pe = _payee_expr('NEW.')
    for when, name in (('BEFORE INSERT', 'ins'), ('BEFORE UPDATE OF payee_type,payee_id,booking_id,experience_booking_id', 'upd')):
        db.execute(f'''CREATE TRIGGER IF NOT EXISTS wod_payment_orders_tenant_{name} {when} ON payment_orders BEGIN
          SELECT RAISE(ABORT, 'WOD: pago sin centro') WHERE NEW.payee_type IS NULL OR NEW.payee_id IS NULL;
          SELECT RAISE(ABORT, 'WOD: el pago y la reserva son de centros distintos')
           WHERE NEW.booking_id IS NOT NULL AND (SELECT provider_id FROM bookings WHERE id=NEW.booking_id) IS NOT {pe};
          SELECT RAISE(ABORT, 'WOD: el pago y la experiencia son de centros distintos')
           WHERE NEW.experience_booking_id IS NOT NULL AND (SELECT e.provider_id FROM experience_bookings eb JOIN travel_experiences e ON e.id=eb.travel_experience_id
                                                             WHERE eb.id=NEW.experience_booking_id) IS NOT {pe};
        END''')
    # Departures: the tenant of their service (kept by triggers; a departure never moves to another tenant).
    if 'provider_id' not in _xcols(db, 'service_slots'):
        db.execute('ALTER TABLE service_slots ADD COLUMN provider_id TEXT REFERENCES providers(id)')
    db.execute('UPDATE service_slots SET provider_id=(SELECT provider_id FROM provider_services s WHERE s.id=service_slots.service_id) WHERE provider_id IS NULL')
    db.execute("UPDATE service_slots SET provider_id='x:0' WHERE provider_id IS NULL")
    report['service_slots'] = db.execute("SELECT COUNT(*) FROM service_slots WHERE provider_id='x:0'").fetchone()[0]
    db.execute('''CREATE TRIGGER IF NOT EXISTS wod_service_slots_tenant_ins AFTER INSERT ON service_slots BEGIN
        UPDATE service_slots SET provider_id=(SELECT provider_id FROM provider_services WHERE id=NEW.service_id) WHERE id=NEW.id;
        SELECT RAISE(ABORT, 'WOD: salida sin centro') WHERE (SELECT provider_id FROM service_slots WHERE id=NEW.id) IS NULL; END''')
    db.execute('''CREATE TRIGGER IF NOT EXISTS wod_service_slots_tenant_upd BEFORE UPDATE OF service_id,provider_id ON service_slots
        WHEN NEW.provider_id IS NOT (SELECT provider_id FROM provider_services WHERE id=NEW.service_id) AND OLD.provider_id IS NOT NULL BEGIN
        SELECT RAISE(ABORT, 'WOD: una salida no puede pasar a otro centro'); END''')
    db.execute(f'''CREATE TRIGGER IF NOT EXISTS wod_provider_services_owner_upd AFTER UPDATE OF center_id,provider_user_id ON provider_services BEGIN
        UPDATE service_slots SET provider_id={owner_expr('center_id', 'provider_user_id', 'NEW.')} WHERE service_id=NEW.id; END''')
    # Consistency: a booking, its service and its departure are of the same tenant; so are the rows that join them.
    be = owner_expr('center_id', 'provider_user_id', 'NEW.')
    for when, name in (('BEFORE INSERT', 'ins'), ('BEFORE UPDATE OF service_id,slot_id,center_id,provider_user_id', 'upd')):
        db.execute(f'''CREATE TRIGGER IF NOT EXISTS wod_bookings_same_tenant_{name} {when} ON bookings BEGIN
          SELECT RAISE(ABORT, 'WOD: la reserva y su servicio son de centros distintos')
           WHERE NEW.service_id IS NOT NULL AND (SELECT provider_id FROM provider_services WHERE id=NEW.service_id) IS NOT {be};
          SELECT RAISE(ABORT, 'WOD: la reserva y su salida son de centros distintos')
           WHERE NEW.slot_id IS NOT NULL AND (SELECT provider_id FROM service_slots WHERE id=NEW.slot_id) IS NOT {be};
        END''')
    pairs = {   # table: (booking column, slot column)
        'manifest_entries': ('booking_id', 'slot_id'), 'slot_cancel_offers': ('booking_id', 'slot_id'), 'reschedule_requests': ('booking_id', 'to_slot_id'),
    }
    for t, (bc, sc) in pairs.items():
        for when, name in (('BEFORE INSERT', 'ins'), (f'BEFORE UPDATE OF {bc},{sc}', 'upd')):
            db.execute(f'''CREATE TRIGGER IF NOT EXISTS wod_{t}_same_tenant_{name} {when} ON {t} BEGIN
              SELECT RAISE(ABORT, 'WOD: reserva y salida de centros distintos ({t})')
               WHERE NEW.{sc} IS NOT NULL AND (SELECT provider_id FROM bookings WHERE id=NEW.{bc}) IS NOT (SELECT provider_id FROM service_slots WHERE id=NEW.{sc});
            END''')
    for when, name in (('BEFORE INSERT', 'ins'), ('BEFORE UPDATE OF boat_id,slot_id', 'upd')):
        db.execute(f'''CREATE TRIGGER IF NOT EXISTS wod_slot_groups_same_tenant_{name} {when} ON slot_groups BEGIN
          SELECT RAISE(ABORT, 'WOD: barco de otro centro')
           WHERE NEW.boat_id IS NOT NULL AND (SELECT provider_id FROM boats WHERE id=NEW.boat_id) IS NOT (SELECT provider_id FROM service_slots WHERE id=NEW.slot_id);
        END''')
    for t, cols in TENANT_INDEXES.items():
        for i, cols_ in enumerate(cols):
            db.execute(f'CREATE INDEX IF NOT EXISTS idx_{t}_tenant{i} ON {t}({cols_})')
    return report


def tenant_of_row(row):
    """The tenant key of a row that has provider_id (or None)."""
    try: return row['provider_id']
    except (IndexError, KeyError): return None
