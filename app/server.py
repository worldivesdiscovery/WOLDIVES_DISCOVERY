#!/usr/bin/env python3
from __future__ import annotations

import base64
import hashlib
import html
import json
import math
import mimetypes
import os
import socket
import re
import secrets
import sqlite3
import unicodedata
import sys
import threading
import time
from datetime import datetime, timezone
from email import policy
from email.parser import BytesParser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse, unquote, quote

ROOT = Path(__file__).resolve().parents[1]
if str(Path(__file__).resolve().parent) not in sys.path: sys.path.insert(0, str(Path(__file__).resolve().parent))
from wod import config as wcfg
from wod import security as wsec
from wod import bookings as wbk
from wod import pdf as wpdf
# Bundled pure-python dependencies (qrcode). Installed packages take precedence.
if str(ROOT/'vendor') not in sys.path: sys.path.append(str(ROOT/'vendor'))
PUBLIC = ROOT / 'public'
DATA = Path(os.environ.get('WOD_DATA_DIR') or (ROOT / 'data'))
STORAGE = Path(os.environ.get('WOD_STORAGE_DIR') or (ROOT / 'storage'))
UPLOADS = STORAGE / 'documents'
# Public images uploaded by centres and the administrator (served at /assets/uploads/…). Outside the code tree in
# production (WOD_UPLOADS_DIR) so deployments and backups treat them as data, not as code.
PHOTOS = Path(os.environ.get('WOD_UPLOADS_DIR') or (PUBLIC / 'assets' / 'uploads'))
DB_PATH = Path(os.environ.get('WOD_DB_PATH') or (DATA / 'worldivesdiscovery.sqlite3'))
LOG_DIR = Path(os.environ.get('WOD_LOG_DIR') or (ROOT / 'logs'))
HOST = os.environ.get('WOD_HOST', '127.0.0.1')
PORT = int(os.environ.get('WOD_PORT', '8000'))
COOKIE = 'wd_session'
APP_VERSION = '50.34'
# G7: JSON bodies up to 1 MB; file uploads up to WOD_MAX_UPLOAD_MB (15 MB). Checked before reading the body.
MAX_BODY = wcfg.MAX_JSON_BYTES
MAX_UPLOAD = wcfg.MAX_UPLOAD_BYTES
SESSION_TTL_SECONDS = int(os.environ.get('WOD_SESSION_TTL_SECONDS', '28800'))
LOGIN_WINDOW_SECONDS = int(os.environ.get('WOD_LOGIN_WINDOW_SECONDS', '900'))
LOGIN_MAX_ATTEMPTS = int(os.environ.get('WOD_LOGIN_MAX_ATTEMPTS', '8'))
# Sessions are stored in the database (table sessions) so they survive restarts and work with several server processes.


ROLES = {'admin', 'center', 'freelance', 'recreational'}

SCHEMA = '''
CREATE TABLE IF NOT EXISTS user_profiles (
  user_id INTEGER PRIMARY KEY,
  phone TEXT,
  country TEXT,
  city TEXT,
  preferred_language TEXT DEFAULT 'es',
  notes TEXT,
  date_of_birth TEXT,
  emergency_contact_name TEXT,
  emergency_contact_phone TEXT,
  equipment_required INTEGER DEFAULT 0,
  suit_type TEXT,
  suit_size TEXT,
  boot_size TEXT,
  bcd_size TEXT,
  fin_size TEXT,
  mask_size TEXT,
  usual_weight_kg REAL,
  tank_preference TEXT,
  computer_preference TEXT,
  equipment_notes TEXT,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS user_documents (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  document_type TEXT NOT NULL,
  title TEXT NOT NULL,
  file_path TEXT NOT NULL,
  original_name TEXT NOT NULL,
  expires_at TEXT,
  status TEXT NOT NULL DEFAULT 'pending',
  uploaded_at TEXT NOT NULL,
  FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS center_links (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  center_id INTEGER NOT NULL,
  first_checkin TEXT NOT NULL,
  last_checkin TEXT NOT NULL,
  UNIQUE(user_id, center_id),
  FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY(center_id) REFERENCES centers(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS qr_codes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  center_id INTEGER NOT NULL,
  code TEXT NOT NULL UNIQUE,
  label TEXT NOT NULL,
  active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  FOREIGN KEY(center_id) REFERENCES centers(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS center_extras (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  center_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  price REAL NOT NULL DEFAULT 0,
  active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(center_id) REFERENCES centers(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_center_extras_center ON center_extras(center_id, active);

CREATE TABLE IF NOT EXISTS bookings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  center_id INTEGER,
  dive_point_id INTEGER,
  booking_date TEXT NOT NULL,
  booking_time TEXT,
  participants INTEGER NOT NULL DEFAULT 1,
  needs_equipment INTEGER NOT NULL DEFAULT 0,
  equipment_items TEXT,
  equipment_notes TEXT,
  needs_guide INTEGER NOT NULL DEFAULT 0,
  guide_notes TEXT,
  nitrox INTEGER NOT NULL DEFAULT 0,
  pickup INTEGER NOT NULL DEFAULT 0,
  notes TEXT,
  status TEXT NOT NULL DEFAULT 'pending',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY(center_id) REFERENCES centers(id) ON DELETE CASCADE,
  FOREIGN KEY(dive_point_id) REFERENCES dive_points(id) ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER,
  action TEXT NOT NULL,
  entity_type TEXT,
  entity_id INTEGER,
  details TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS center_reviews (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  center_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
  title TEXT,
  body TEXT,
  active INTEGER NOT NULL DEFAULT 1,
  verified INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(center_id,user_id),
  FOREIGN KEY(center_id) REFERENCES centers(id) ON DELETE CASCADE,
  FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_center_reviews_center ON center_reviews(center_id, active, created_at DESC);
CREATE TABLE IF NOT EXISTS travel_offers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  region TEXT NOT NULL,
  kind TEXT NOT NULL,
  image_path TEXT,
  summary TEXT,
  active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS travel_experiences (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  travel_offer_id INTEGER NOT NULL,
  title TEXT NOT NULL,
  provider_user_id INTEGER,
  center_id INTEGER,
  provider_type TEXT NOT NULL DEFAULT 'center',
  summary TEXT,
  description TEXT,
  start_date TEXT,
  end_date TEXT,
  price REAL,
  currency TEXT NOT NULL DEFAULT 'EUR',
  spots_total INTEGER,
  spots_available INTEGER,
  includes TEXT,
  conditions TEXT,
  status TEXT NOT NULL DEFAULT 'pending',
  active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(travel_offer_id) REFERENCES travel_offers(id) ON DELETE CASCADE,
  FOREIGN KEY(provider_user_id) REFERENCES users(id) ON DELETE SET NULL,
  FOREIGN KEY(center_id) REFERENCES centers(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_travel_experiences_destination ON travel_experiences(travel_offer_id, active, status);
CREATE INDEX IF NOT EXISTS idx_travel_experiences_provider ON travel_experiences(provider_user_id, active);
CREATE TABLE IF NOT EXISTS experience_bookings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  travel_experience_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  participants INTEGER NOT NULL DEFAULT 1,
  notes TEXT,
  status TEXT NOT NULL DEFAULT 'requested',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(travel_experience_id) REFERENCES travel_experiences(id) ON DELETE CASCADE,
  FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sender_user_id INTEGER NOT NULL,
  recipient_user_id INTEGER NOT NULL,
  booking_id INTEGER,
  experience_booking_id INTEGER,
  subject TEXT NOT NULL,
  body TEXT NOT NULL,
  created_at TEXT NOT NULL,
  read_at TEXT,
  FOREIGN KEY(sender_user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY(recipient_user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY(booking_id) REFERENCES bookings(id) ON DELETE SET NULL,
  FOREIGN KEY(experience_booking_id) REFERENCES experience_bookings(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_messages_recipient ON messages(recipient_user_id, created_at DESC);
CREATE TABLE IF NOT EXISTS virtual_experiences (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  dive_point_id INTEGER NOT NULL,
  title TEXT NOT NULL,
  experience_type TEXT NOT NULL DEFAULT 'panorama',
  provider TEXT,
  url TEXT,
  media_path TEXT,
  description TEXT,
  duration_seconds INTEGER,
  active INTEGER NOT NULL DEFAULT 1,
  created_by_user_id INTEGER,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(dive_point_id) REFERENCES dive_points(id) ON DELETE CASCADE,
  FOREIGN KEY(created_by_user_id) REFERENCES users(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_virtual_experiences_point ON virtual_experiences(dive_point_id, active, id);
CREATE INDEX IF NOT EXISTS idx_user_documents_user ON user_documents(user_id, expires_at);
CREATE INDEX IF NOT EXISTS idx_bookings_center ON bookings(center_id, booking_date, status);
CREATE INDEX IF NOT EXISTS idx_bookings_user ON bookings(user_id, booking_date DESC);
CREATE INDEX IF NOT EXISTS idx_center_links_center ON center_links(center_id, last_checkin DESC);
CREATE TABLE IF NOT EXISTS wallet_transactions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  amount REAL NOT NULL,
  description TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS rewards (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER,
  title TEXT NOT NULL,
  description TEXT,
  points INTEGER NOT NULL DEFAULT 0,
  completed INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS reward_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  event_key TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  points INTEGER NOT NULL DEFAULT 0,
  wallet_amount REAL NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  UNIQUE(user_id, event_key),
  FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_reward_events_user ON reward_events(user_id, created_at DESC);
CREATE TABLE IF NOT EXISTS reward_offers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  center_id INTEGER,
  title TEXT NOT NULL,
  description TEXT,
  reward_type TEXT NOT NULL DEFAULT 'discount',
  cost_wallet REAL NOT NULL DEFAULT 0,
  value_text TEXT,
  conditions TEXT,
  stock INTEGER,
  active INTEGER NOT NULL DEFAULT 1,
  created_by_user_id INTEGER,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(center_id) REFERENCES centers(id) ON DELETE SET NULL,
  FOREIGN KEY(created_by_user_id) REFERENCES users(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_reward_offers_center ON reward_offers(center_id, active);
CREATE TABLE IF NOT EXISTS reward_redemptions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  offer_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  code TEXT NOT NULL UNIQUE,
  cost_wallet REAL NOT NULL,
  status TEXT NOT NULL DEFAULT 'issued',
  created_at TEXT NOT NULL,
  redeemed_at TEXT,
  FOREIGN KEY(offer_id) REFERENCES reward_offers(id) ON DELETE CASCADE,
  FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_reward_redemptions_user ON reward_redemptions(user_id, created_at DESC);
CREATE TABLE IF NOT EXISTS provider_services (
 id INTEGER PRIMARY KEY AUTOINCREMENT, provider_user_id INTEGER NOT NULL, center_id INTEGER,
 service_type TEXT NOT NULL DEFAULT 'inmersion', title TEXT NOT NULL, description TEXT,
 duration_minutes INTEGER, price REAL NOT NULL DEFAULT 0, currency TEXT NOT NULL DEFAULT 'EUR',
 max_participants INTEGER, booking_mode TEXT NOT NULL DEFAULT 'request', active INTEGER NOT NULL DEFAULT 1,
 color TEXT DEFAULT '#2563eb',
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
 FOREIGN KEY(provider_user_id) REFERENCES users(id) ON DELETE CASCADE,
 FOREIGN KEY(center_id) REFERENCES centers(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_provider_services_provider ON provider_services(provider_user_id, active);
CREATE TABLE IF NOT EXISTS service_slots (
 id INTEGER PRIMARY KEY AUTOINCREMENT, service_id INTEGER NOT NULL, slot_date TEXT NOT NULL, slot_time TEXT NOT NULL,
 spots_total INTEGER NOT NULL DEFAULT 1, spots_available INTEGER NOT NULL DEFAULT 1, status TEXT NOT NULL DEFAULT 'open',
 point_mode TEXT NOT NULL DEFAULT 'fixed',
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL, UNIQUE(service_id, slot_date, slot_time),
 FOREIGN KEY(service_id) REFERENCES provider_services(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_service_slots_service ON service_slots(service_id, slot_date, slot_time);
CREATE TABLE IF NOT EXISTS center_point_links (
 id INTEGER PRIMARY KEY AUTOINCREMENT, center_id INTEGER NOT NULL, dive_point_id INTEGER NOT NULL, created_at TEXT NOT NULL,
 UNIQUE(center_id,dive_point_id), FOREIGN KEY(center_id) REFERENCES centers(id) ON DELETE CASCADE, FOREIGN KEY(dive_point_id) REFERENCES dive_points(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_center_point_links_center ON center_point_links(center_id);
CREATE TABLE IF NOT EXISTS center_equipment (
 id INTEGER PRIMARY KEY AUTOINCREMENT, center_id INTEGER NOT NULL, code TEXT NOT NULL, label TEXT NOT NULL, price REAL,
 active INTEGER NOT NULL DEFAULT 1, sort_order INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL,
 UNIQUE(center_id,code), FOREIGN KEY(center_id) REFERENCES centers(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_center_equipment_center ON center_equipment(center_id);
CREATE TABLE IF NOT EXISTS service_slot_points (
 slot_id INTEGER NOT NULL, dive_point_id INTEGER NOT NULL, PRIMARY KEY(slot_id,dive_point_id),
 FOREIGN KEY(slot_id) REFERENCES service_slots(id) ON DELETE CASCADE, FOREIGN KEY(dive_point_id) REFERENCES dive_points(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_service_slot_points_slot ON service_slot_points(slot_id);
CREATE TABLE IF NOT EXISTS payment_orders (
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, provider_user_id INTEGER, booking_id INTEGER,
 experience_booking_id INTEGER, service_id INTEGER, amount REAL NOT NULL, currency TEXT NOT NULL DEFAULT 'EUR',
 status TEXT NOT NULL DEFAULT 'pending', provider TEXT NOT NULL DEFAULT 'stripe', provider_payment_id TEXT,
 checkout_url TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
 FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
 FOREIGN KEY(provider_user_id) REFERENCES users(id) ON DELETE SET NULL,
 FOREIGN KEY(booking_id) REFERENCES bookings(id) ON DELETE SET NULL,
 FOREIGN KEY(experience_booking_id) REFERENCES experience_bookings(id) ON DELETE SET NULL,
 FOREIGN KEY(service_id) REFERENCES provider_services(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_payment_orders_user ON payment_orders(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_payment_orders_booking ON payment_orders(booking_id);
CREATE TABLE IF NOT EXISTS center_integrations (
 id INTEGER PRIMARY KEY AUTOINCREMENT, center_id INTEGER NOT NULL UNIQUE, api_key_hash TEXT NOT NULL, api_key_prefix TEXT NOT NULL, enabled INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
 FOREIGN KEY(center_id) REFERENCES centers(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_center_integrations_center ON center_integrations(center_id);
CREATE TABLE IF NOT EXISTS stripe_webhook_events (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 event_id TEXT NOT NULL UNIQUE,
 event_type TEXT NOT NULL,
 created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS service_templates (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  provider_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  service_type TEXT NOT NULL DEFAULT 'inmersion',
  title TEXT,
  description TEXT,
  duration_minutes INTEGER,
  max_participants INTEGER,
  booking_mode TEXT NOT NULL DEFAULT 'request',
  color TEXT,
  price REAL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_service_templates_provider ON service_templates(provider_user_id, name);
CREATE TABLE IF NOT EXISTS sessions (
  token_hash TEXT PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at REAL NOT NULL,
  last_seen REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_last_seen ON sessions(last_seen);
'''



# Rate limits: thread-safe and bounded in size (wod.security.RateLimiter).
LOGIN_LIMIT = wsec.RateLimiter(LOGIN_MAX_ATTEMPTS, LOGIN_WINDOW_SECONDS)
LOGIN_IP_LIMIT = wsec.RateLimiter(LOGIN_MAX_ATTEMPTS * 5, LOGIN_WINDOW_SECONDS)
NOTICE_LIMIT = wsec.RateLimiter(60, 3600)
REGISTER_LIMIT = wsec.RateLimiter(wcfg.env_int('WOD_REGISTER_MAX_PER_HOUR', 10, 1), 3600)
FORGOT_LIMIT = wsec.RateLimiter(5, 900)
TOTP_LIMIT = wsec.RateLimiter(6, 900)
GEOCODE_LIMIT = wsec.RateLimiter(30, 60)
INFO_LIMIT = wsec.RateLimiter(10, 3600)

PRIVATE_USER_FIELDS = ('password_hash', 'totp_secret', 'totp_pending_secret', 'email_verify_token')

def public_user(user):
    if not user:
        return None
    d = dict(user)
    for k in PRIVATE_USER_FIELDS: d.pop(k, None)
    return d

def login_rate_limited(key):
    return LOGIN_LIMIT.blocked(key)

def record_login_failure(key):
    LOGIN_LIMIT.hit(key)

def clear_login_failures(key):
    LOGIN_LIMIT.reset(key)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


class _ClosingConnection(sqlite3.Connection):
    """`with connect() as db:` commits or rolls back AND closes the connection at the end of the request."""
    def __exit__(self, exc_type, exc, tb):
        try:
            return super().__exit__(exc_type, exc, tb)
        finally:
            self.close()


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH, factory=_ClosingConnection)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    # WAL is persistent (set once in bootstrap); NORMAL sync is safe in WAL mode and much faster for writes.
    db.execute('PRAGMA synchronous=NORMAL')
    db.execute('PRAGMA busy_timeout=10000')
    # fold(): lower-case without accents, so «maria» finds «María».
    db.create_function('fold', 1, fold_text, deterministic=True)
    return db


def log_exception(handler, exc):
    """Unexpected errors go to stderr with the request line (without the query string: it may hold searches or
    coordinates) so they can be traced in production logs. Repeated errors raise an alert (see wod.ops)."""
    import traceback
    try: sys.stderr.write(f"[{datetime.now().isoformat(timespec='seconds')}] {handler.command} {urlparse(handler.path).path} -> {type(exc).__name__}: {exc}\n" + ''.join(traceback.format_exception(exc)[-3:]))
    except Exception: pass
    try: ERROR_MONITOR.record(urlparse(handler.path).path, exc)
    except Exception: pass


class _NullWriter:
    def write(self, data): return len(data)
    def flush(self): pass


PUBLIC_ROOT_FILES = {'/sw.js':'application/javascript; charset=utf-8','/manifest.webmanifest':'application/manifest+json','/robots.txt':'text/plain; charset=utf-8'}


def fold_text(value):
    if value is None: return ''
    return ''.join(ch for ch in unicodedata.normalize('NFKD', str(value).lower()) if not unicodedata.combining(ch))


CURATED_POINTS_V30 = [
    # name, dive_type, lat, lon, difficulty, min_depth, max_depth, access, subregion, description
    ('La Barra (Les Marines)', 'Arrecife · Fondo rocoso', 38.86187, 0.11197, 'Fácil', None, 15,
     'Barco desde Dénia', 'Marina Alta · Dénia',
     'Bajos rocosos frente a Les Marines, al norte del puerto de Dénia: lajas, grietas y escalones de roca con vida abundante sobre fondo de arena. Profundidad máxima de unos 15 m; inmersión sencilla.'),
    ('La Cullerà', 'Cueva · Pared', 38.811389, 0.182903, 'Intermedia', 9, 15,
     'Barco · Reserva Marina del Cabo de San Antonio: autorización previa', 'Marina Alta · Dénia',
     'Dentro de la Reserva Marina del Cabo de San Antonio. Se entra por una pequeña garganta al pie del acantilado, a unos 9 m, hasta una gran cueva de unos 50 m (imprescindible linterna). En la zona abierta, entre 10 y 15 m, rocas con pulpos, dentones y corvinas. Necesita autorización previa de la reserva.'),
    ('Les Rotes · El Fresquito', 'Arrecife · Pared', 38.82345, 0.159433, 'Fácil', 3, 10,
     'Orilla (bajada a una poza natural)', 'Marina Alta · Dénia',
     'Ruta desde la costa rocosa de Les Rotes, al sur de Dénia, siguiendo una pared de roca con pulpos, gusanos tubícolas y morenas. Empieza a unos 3 m y llega a unos 10 m. También es un buen punto de snorkel, con arcos a unos 4 m.'),
    ('El Tangó', 'Arrecife · Posidonia', 38.799898, 0.190415, 'Fácil', None, None,
     'Orilla, junto al puerto de Xàbia', 'Marina Alta · Xàbia',
     'Cala de poca profundidad junto al dique del puerto de Xàbia, con pradera de posidonia y lenguas de roca. Morenas, pulpos y salpas. Inmersión fácil desde la orilla y muy buen snorkel.'),
    ("María Claudia (Mona de l'Illa)", 'Pared · Chimenea · Bloques', 38.752255, 0.231217, 'Intermedia', 7, 22,
     'Barco (fondeo junto al islote)', 'Marina Alta · Xàbia',
     "Inmersión alrededor del islote de la Mona de l'Illa. Se entra por una chimenea que va de unos 11 a 7 m, con juegos de luz, y se recorre un fondo de arena con grandes bloques entre 15 y 22 m."),
    ('Escull de Sant Pere (El Bergantí)', 'Pared · Cueva', 38.742467, 0.233333, 'Avanzado', None, 32,
     'Barco desde Xàbia', 'Marina Alta · Xàbia',
     'Bajo rocoso frente al cabo Negre con una cueva en forma de L de unos 25 m de recorrido, cuya entrada está a unos 22 m. Profundidad máxima de unos 32 m. Para buceadores avanzados.'),
    ('Isla del Descubridor', 'Pared · Túneles', 38.726667, 0.218056, 'Fácil', None, None,
     'Barco desde Xàbia', 'Marina Alta · Xàbia',
     'Islote junto a los acantilados del cabo de la Nao. Pared con túneles y pasos entre rocas, con una profundidad media de unos 14 m. Inmersión sencilla.'),
    ('La Granadella', 'Arrecife · Arco · Posidonia', 38.729355, 0.196434, 'Fácil', None, 10,
     'Orilla, desde la playa de la Granadella', 'Marina Alta · Xàbia',
     'Desde la playa de la Granadella: un pequeño arco a unos 3 m, rocas y posidonia y, a la vuelta, una serie de pequeñas cuevas junto a la pared. Unos 10 m de máximo; apta para todos los niveles y para snorkel.'),
    ('El Moraig · Cova dels Arcs', 'Cueva · Pared', 38.709826, 0.166764, 'Avanzado', 5, 14,
     'Orilla, desde la cala del Moraig', 'Marina Alta · Benitatxell',
     'Se baja por una escalera hasta una cueva y una poza; un paso estrecho lleva a mar abierto y se sigue la pared hasta una gran cueva con luz cenital y una haloclina. Para buceadores con experiencia. No hay que entrar en la galería del río subterráneo.'),
    ('Acantilados del Mascarat (La Bodega)', 'Pared · Túnel · Arcos', 38.628056, 0.005833, 'Intermedia', None, 27,
     'Barco desde Calp o Altea', 'Marina Alta y Baixa · Calpe',
     'Pared del acantilado del Mascarat, entre Calp y Altea, con un túnel, arcos y una chimenea. Gorgonias y, a menudo, barracudas. Profundidad máxima de unos 27 m.'),
]


def seed_curated_points_v30(db):
    have={r['name'] for r in db.execute('SELECT name FROM dive_points').fetchall()}
    for name,dtype,lat,lon,diff,dmin,dmax,access,sub,desc in CURATED_POINTS_V30:
        if name in have: continue
        db.execute("""INSERT INTO dive_points(name,country,region,dive_type,latitude,longitude,difficulty,min_depth,max_depth,description,access_info,zone,subregion,
                      verification_status,data_confidence,active,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1,?,?)""",
                   (name,'España','Comunitat Valenciana',dtype,lat,lon,diff,dmin,dmax,desc,access,'Europa',sub,'curated_pending','curated',now(),now()))


def bootstrap():
    with connect() as db:
        db.execute('PRAGMA journal_mode=WAL')
        db.executescript(SCHEMA)
        # Reviews are tied to a real completed booking at the center.
        db.execute('CREATE INDEX IF NOT EXISTS idx_center_reviews_user ON center_reviews(user_id, center_id)')
        # Migrations for the evolving WORLDIVES DISCOVERY prototype.
        user_cols={r['name'] for r in db.execute('PRAGMA table_info(users)').fetchall()}
        if 'requested_role' not in user_cols:
            db.execute("ALTER TABLE users ADD COLUMN requested_role TEXT DEFAULT 'recreational'")
        if 'provider_bio' not in user_cols:
            db.execute("ALTER TABLE users ADD COLUMN provider_bio TEXT")
        if 'avatar_url' not in user_cols: db.execute('ALTER TABLE users ADD COLUMN avatar_url TEXT')
        for _col in ['instagram_url','facebook_url','twitter_url','youtube_url','tiktok_url']:
            if _col not in user_cols: db.execute(f'ALTER TABLE users ADD COLUMN {_col} TEXT')
        profile_cols={r['name'] for r in db.execute('PRAGMA table_info(user_profiles)').fetchall()}
        profile_migrations={'certification_id':'INTEGER','date_of_birth':'TEXT','emergency_contact_name':'TEXT','emergency_contact_phone':'TEXT','equipment_required':'INTEGER DEFAULT 0','suit_type':'TEXT','suit_size':'TEXT','boot_size':'TEXT','bcd_size':'TEXT','fin_size':'TEXT','mask_size':'TEXT','usual_weight_kg':'REAL','tank_preference':'TEXT','computer_preference':'TEXT','equipment_notes':'TEXT'}
        for _col,_typ in profile_migrations.items():
            if _col not in profile_cols: db.execute(f'ALTER TABLE user_profiles ADD COLUMN {_col} {_typ}')
        point_cols={r['name'] for r in db.execute('PRAGMA table_info(dive_points)').fetchall()}
        if 'recommended_certification_id' not in point_cols:
            db.execute('ALTER TABLE dive_points ADD COLUMN recommended_certification_id INTEGER')
        logbook_cols={r['name'] for r in db.execute('PRAGMA table_info(logbook_entries)').fetchall()}
        if 'booking_id' not in logbook_cols:
            db.execute('ALTER TABLE logbook_entries ADD COLUMN booking_id INTEGER')
        db.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_logbook_booking ON logbook_entries(booking_id) WHERE booking_id IS NOT NULL')
        # Associate existing center-owned points with the new reusable center catalog.
        db.execute('INSERT OR IGNORE INTO center_point_links(center_id,dive_point_id,created_at) SELECT center_id,id,? FROM dive_points WHERE center_id IS NOT NULL AND active=1',(now(),))
        center_cols={r['name'] for r in db.execute('PRAGMA table_info(centers)').fetchall()}
        for _col,_typ in [('source_name','TEXT'),('source_url','TEXT'),('verification_status',"TEXT DEFAULT 'source_public'"),('data_confidence',"TEXT DEFAULT 'public'"),('instagram_url','TEXT'),('facebook_url','TEXT'),('twitter_url','TEXT'),('youtube_url','TEXT'),('tiktok_url','TEXT')]:
            if _col not in center_cols: db.execute(f'ALTER TABLE centers ADD COLUMN {_col} {_typ}')
        # Stripe Connect: the connected account ID is the only payment-provider
        # identifier stored locally. Sensitive KYC/bank data remains with Stripe.
        for _col,_typ in [('stripe_account_id','TEXT'),('stripe_charges_enabled','INTEGER DEFAULT 0'),('stripe_payouts_enabled','INTEGER DEFAULT 0'),('stripe_details_submitted','INTEGER DEFAULT 0')]:
            if _col not in center_cols: db.execute(f'ALTER TABLE centers ADD COLUMN {_col} {_typ}')
        qr_cols={r['name'] for r in db.execute('PRAGMA table_info(qr_codes)').fetchall()}
        for _col,_typ in [('purpose',"TEXT DEFAULT 'center'"),('reference_id','INTEGER')]:
            if _col not in qr_cols: db.execute(f'ALTER TABLE qr_codes ADD COLUMN {_col} {_typ}')
        # Indexes for the queries that grow with the number of centers and bookings.
        for _idx in ["CREATE INDEX IF NOT EXISTS idx_provider_services_center ON provider_services(center_id, active)",
                     "CREATE INDEX IF NOT EXISTS idx_bookings_slot ON bookings(slot_id)",
                     "CREATE INDEX IF NOT EXISTS idx_bookings_service ON bookings(service_id)",
                     "CREATE INDEX IF NOT EXISTS idx_experience_bookings_exp ON experience_bookings(travel_experience_id, status)",
                     "CREATE INDEX IF NOT EXISTS idx_payment_orders_provider ON payment_orders(provider_user_id, created_at DESC)",
                     "CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_log(entity_type, entity_id)",
                     "CREATE INDEX IF NOT EXISTS idx_users_email ON users(lower(email))",
                     "CREATE INDEX IF NOT EXISTS idx_center_links_user ON center_links(user_id)"]:
            db.execute(_idx)
        # Center showcase (public page) customisation.
        for _col,_typ in [('cover_url','TEXT'),('tagline','TEXT'),('gallery_json','TEXT'),('languages','TEXT'),('opening_hours','TEXT')]:
            if _col not in center_cols: db.execute(f'ALTER TABLE centers ADD COLUMN {_col} {_typ}')
        migrate_center_directory_data(db)
        db.execute('CREATE TABLE IF NOT EXISTS site_media (key TEXT PRIMARY KEY, image_url TEXT, credit TEXT, updated_at TEXT, updated_by INTEGER)')
        db.execute('''CREATE TABLE IF NOT EXISTS promotions (id INTEGER PRIMARY KEY AUTOINCREMENT, center_id INTEGER NOT NULL, created_by INTEGER,
          title TEXT NOT NULL, description TEXT, value_text TEXT, conditions TEXT, valid_from TEXT, valid_until TEXT NOT NULL,
          uses_per_code INTEGER NOT NULL DEFAULT 1, status TEXT NOT NULL DEFAULT 'active', created_at TEXT NOT NULL, updated_at TEXT NOT NULL)''')
        db.execute('''CREATE TABLE IF NOT EXISTS promotion_partners (promotion_id INTEGER NOT NULL, center_id INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'invited',
          updated_at TEXT NOT NULL, PRIMARY KEY(promotion_id,center_id))''')
        db.execute('''CREATE TABLE IF NOT EXISTS promotion_codes (id INTEGER PRIMARY KEY AUTOINCREMENT, promotion_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
          code TEXT NOT NULL UNIQUE, status TEXT NOT NULL DEFAULT 'active', uses INTEGER NOT NULL DEFAULT 0, created_by INTEGER, created_at TEXT NOT NULL, revoked_at TEXT)''')
        db.execute('''CREATE TABLE IF NOT EXISTS promotion_redemptions (id INTEGER PRIMARY KEY AUTOINCREMENT, code_id INTEGER NOT NULL, center_id INTEGER NOT NULL,
          redeemed_by INTEGER, note TEXT, created_at TEXT NOT NULL)''')
        db.execute('CREATE INDEX IF NOT EXISTS idx_promotions_center ON promotions(center_id,status)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_promo_codes_user ON promotion_codes(user_id)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_promo_codes_promo ON promotion_codes(promotion_id)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_promo_partners_center ON promotion_partners(center_id,status)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_promo_redemptions_code ON promotion_redemptions(code_id)')
        db.execute('''CREATE TABLE IF NOT EXISTS site_themes (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, accent TEXT NOT NULL DEFAULT 'oceano',
          ribbon TEXT, mode TEXT NOT NULL DEFAULT 'schedule', scope TEXT NOT NULL DEFAULT 'all', starts_on TEXT, ends_on TEXT,
          created_at TEXT NOT NULL, updated_at TEXT NOT NULL, updated_by INTEGER)''')
        db.execute('''CREATE TABLE IF NOT EXISTS site_theme_media (theme_id INTEGER NOT NULL REFERENCES site_themes(id) ON DELETE CASCADE, key TEXT NOT NULL,
          image_url TEXT NOT NULL, credit TEXT, updated_at TEXT NOT NULL, PRIMARY KEY(theme_id,key))''')
        db.execute('''CREATE TABLE IF NOT EXISTS site_promos (id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL DEFAULT 'partner', title TEXT NOT NULL,
          subtitle TEXT, label TEXT, url TEXT, image_path TEXT, starts_on TEXT, ends_on TEXT, sort_order INTEGER NOT NULL DEFAULT 0,
          active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)''')
        db.execute('CREATE INDEX IF NOT EXISTS idx_site_promos_active ON site_promos(active, kind, sort_order)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_bookings_date ON bookings(booking_date DESC, id DESC)')
        db.execute('CREATE TABLE IF NOT EXISTS site_settings (key TEXT PRIMARY KEY, value TEXT, updated_at TEXT, updated_by INTEGER)')
        # v50.30: automatic emails, password reset, legal acceptance, cancellations and refunds, content reports.
        db.execute('''CREATE TABLE IF NOT EXISTS email_outbox (id INTEGER PRIMARY KEY AUTOINCREMENT, template TEXT NOT NULL, lang TEXT NOT NULL DEFAULT 'es',
          to_email TEXT NOT NULL, to_name TEXT, subject TEXT NOT NULL, html TEXT, text TEXT, status TEXT NOT NULL DEFAULT 'queued', related_type TEXT, related_id INTEGER,
          attempts INTEGER NOT NULL DEFAULT 0, last_error TEXT, next_try_at TEXT, sent_at TEXT, created_at TEXT NOT NULL)''')
        db.execute('CREATE INDEX IF NOT EXISTS idx_email_outbox_status ON email_outbox(status, next_try_at, id)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_email_outbox_related ON email_outbox(related_type, related_id)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_email_outbox_created ON email_outbox(created_at)')
        db.execute('CREATE TABLE IF NOT EXISTS email_digest_log (center_id INTEGER NOT NULL, digest_date TEXT NOT NULL, sent_at TEXT, PRIMARY KEY(center_id,digest_date))')
        db.execute('''CREATE TABLE IF NOT EXISTS password_resets (token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          expires_at TEXT NOT NULL, used_at TEXT, created_at TEXT NOT NULL)''')
        db.execute('CREATE INDEX IF NOT EXISTS idx_password_resets_user ON password_resets(user_id)')
        db.execute('''CREATE TABLE IF NOT EXISTS content_reports (id INTEGER PRIMARY KEY AUTOINCREMENT, reason TEXT NOT NULL, target_url TEXT, details TEXT NOT NULL,
          reporter_name TEXT, reporter_email TEXT, user_id INTEGER, ip_hash TEXT, status TEXT NOT NULL DEFAULT 'open', resolution TEXT, resolved_by INTEGER, resolved_at TEXT, created_at TEXT NOT NULL)''')
        db.execute('CREATE INDEX IF NOT EXISTS idx_content_reports_status ON content_reports(status, id DESC)')
        _uc={r['name'] for r in db.execute('PRAGMA table_info(users)').fetchall()}
        for _col in ('terms_version','terms_accepted_at','pro_terms_version','pro_terms_accepted_at'):
            if _col not in _uc: db.execute(f'ALTER TABLE users ADD COLUMN {_col} TEXT')
        _bc={r['name'] for r in db.execute('PRAGMA table_info(bookings)').fetchall()}
        for _col,_typ in [('reminder_sent_at','TEXT'),('review_asked_at','TEXT'),('terms_version','TEXT'),('cancelled_at','TEXT'),('cancelled_by','TEXT'),('refund_amount','REAL')]:
            if _col not in _bc: db.execute(f'ALTER TABLE bookings ADD COLUMN {_col} {_typ}')
        # Existing bookings already in the past never get a late reminder or review request.
        seed_curated_points_v30(db)
        if 'reminder_sent_at' not in _bc:
            db.execute("UPDATE bookings SET reminder_sent_at='legacy', review_asked_at='legacy' WHERE booking_date<=date('now','+1 day')")
        db.execute('CREATE INDEX IF NOT EXISTS idx_bookings_reminders ON bookings(booking_date, status)')
        _cc={r['name'] for r in db.execute('PRAGMA table_info(centers)').fetchall()}
        for _col,_typ in [('cancellation_policy',"TEXT DEFAULT 'moderada'"),('cancellation_note','TEXT')]:
            if _col not in _cc: db.execute(f'ALTER TABLE centers ADD COLUMN {_col} {_typ}')
        _pc={r['name'] for r in db.execute('PRAGMA table_info(payment_orders)').fetchall()}
        for _col,_typ in [('refund_id','TEXT'),('refund_amount','REAL'),('refunded_at','TEXT')]:
            if _col not in _pc: db.execute(f'ALTER TABLE payment_orders ADD COLUMN {_col} {_typ}')
        if 'uploaded_by' not in {r['name'] for r in db.execute('PRAGMA table_info(dive_point_photos)').fetchall()}:
            db.execute('ALTER TABLE dive_point_photos ADD COLUMN uploaded_by INTEGER')
        db.execute('CREATE INDEX IF NOT EXISTS idx_centers_active_country ON centers(active, country)')
        # (status, slot_date) index misled the planner away from idx_service_slots_service on per-service lookups.
        db.execute('DROP INDEX IF EXISTS idx_service_slots_open_date')
        db.execute('CREATE INDEX IF NOT EXISTS idx_center_reviews_center ON center_reviews(center_id, active)')
        # Trips sold as a service can be published automatically as an Experience.
        exp_cols={r['name'] for r in db.execute('PRAGMA table_info(travel_experiences)').fetchall()}
        for _col,_typ in [('service_id','INTEGER'),('image_url','TEXT')]:
            if _col not in exp_cols: db.execute(f'ALTER TABLE travel_experiences ADD COLUMN {_col} {_typ}')
        db.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_travel_experiences_service ON travel_experiences(service_id) WHERE service_id IS NOT NULL')
        eb_cols={r['name'] for r in db.execute('PRAGMA table_info(experience_bookings)').fetchall()}
        if 'updated_by' not in eb_cols: db.execute('ALTER TABLE experience_bookings ADD COLUMN updated_by INTEGER')
        # Booking origin and walk-in contact data for bookings entered by the center.
        booking_cols2={r['name'] for r in db.execute('PRAGMA table_info(bookings)').fetchall()}
        for _col,_typ in [('source',"TEXT DEFAULT 'online'"),('contact_phone','TEXT'),('created_by_user_id','INTEGER'),('payment_method','TEXT'),('internal_notes','TEXT')]:
            if _col not in booking_cols2: db.execute(f'ALTER TABLE bookings ADD COLUMN {_col} {_typ}')
        db.execute("UPDATE bookings SET source='web' WHERE external_ref IS NOT NULL AND (source IS NULL OR source='online')")
        service_cols={r['name'] for r in db.execute('PRAGMA table_info(provider_services)').fetchall()}
        if 'color' not in service_cols: db.execute("ALTER TABLE provider_services ADD COLUMN color TEXT DEFAULT '#2563eb'")
        slot_cols={r['name'] for r in db.execute('PRAGMA table_info(service_slots)').fetchall()}
        if 'point_mode' not in slot_cols: db.execute("ALTER TABLE service_slots ADD COLUMN point_mode TEXT NOT NULL DEFAULT 'fixed'")
        db.execute('''CREATE TABLE IF NOT EXISTS center_tariffs (
          id INTEGER PRIMARY KEY AUTOINCREMENT, center_id INTEGER NOT NULL, service_id INTEGER NOT NULL,
          price REAL NOT NULL DEFAULT 0, currency TEXT NOT NULL DEFAULT 'EUR', effective_from TEXT NOT NULL,
          active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
          FOREIGN KEY(center_id) REFERENCES centers(id) ON DELETE CASCADE,
          FOREIGN KEY(service_id) REFERENCES provider_services(id) ON DELETE CASCADE
        )''')
        db.execute('CREATE INDEX IF NOT EXISTS idx_center_tariffs_service ON center_tariffs(center_id,service_id,effective_from)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_center_tariffs_active ON center_tariffs(center_id,active,effective_from)')
        payment_cols={r['name'] for r in db.execute('PRAGMA table_info(payment_orders)').fetchall()}
        for _col,_typ in [('platform_fee','REAL DEFAULT 0'),('connected_account_id','TEXT')]:
            if _col not in payment_cols: db.execute(f'ALTER TABLE payment_orders ADD COLUMN {_col} {_typ}')

        payment_cols={r['name'] for r in db.execute('PRAGMA table_info(payment_orders)').fetchall()}
        if 'slot_id' not in payment_cols: db.execute('ALTER TABLE payment_orders ADD COLUMN slot_id INTEGER')
        for _col,_typ in [('paid_at','TEXT'),('amount_received','REAL'),('receipt_url','TEXT'),('card_brand','TEXT'),('card_last4','TEXT'),('hold_reserved','INTEGER')]:
            if _col not in payment_cols: db.execute(f'ALTER TABLE payment_orders ADD COLUMN {_col} {_typ}')
        db.execute('CREATE INDEX IF NOT EXISTS idx_payment_orders_booking ON payment_orders(booking_id,status)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_payment_orders_status ON payment_orders(status,created_at)')
        booking_cols={r['name'] for r in db.execute('PRAGMA table_info(bookings)').fetchall()}
        for _col,_typ in [('service_id','INTEGER'),('slot_id','INTEGER'),('slot_reserved','INTEGER DEFAULT 0'),('price','REAL DEFAULT 0'),('currency',"TEXT DEFAULT 'EUR'"),('payment_status',"TEXT DEFAULT 'not_required'"),('price_breakdown','TEXT')]:
            if _col not in booking_cols: db.execute(f'ALTER TABLE bookings ADD COLUMN {_col} {_typ}')
        if 'external_ref' not in booking_cols:
            db.execute("ALTER TABLE bookings ADD COLUMN external_ref TEXT")
        db.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_bookings_external_ref ON bookings(center_id, external_ref) WHERE external_ref IS NOT NULL')
        # Link older service bookings to their matching scheduled slot when possible.
        db.execute('''UPDATE bookings SET slot_id=(SELECT ss.id FROM service_slots ss WHERE ss.service_id=bookings.service_id AND ss.slot_date=bookings.booking_date AND ss.slot_time=bookings.booking_time LIMIT 1) WHERE slot_id IS NULL AND service_id IS NOT NULL''')
        travel_cols={r['name'] for r in db.execute('PRAGMA table_info(travel_offers)').fetchall()}
        if 'description' not in travel_cols:
            db.execute("ALTER TABLE travel_offers ADD COLUMN description TEXT")
        # Any reservation already completed before this version is imported once into the user's Log Book.
        completed=db.execute('''SELECT b.id,b.user_id,b.booking_date,b.booking_time,c.name AS center_name,p.name AS point_name,p.country,p.dive_type
                               FROM bookings b LEFT JOIN centers c ON c.id=b.center_id LEFT JOIN dive_points p ON p.id=b.dive_point_id
                               WHERE b.status='completed' AND NOT EXISTS (SELECT 1 FROM logbook_entries l WHERE l.booking_id=b.id)''').fetchall()
        for b in completed:
            site=b['point_name'] or b['center_name']
            note=f"Inmersión generada automáticamente desde la reserva #{b['id']} · {b['center_name']}"
            db.execute('INSERT INTO logbook_entries(user_id,dive_date,site,country,depth,duration,dive_type,notes,created_at,booking_id) VALUES(?,?,?,?,?,?,?,?,?,?)',(b['user_id'],b['booking_date'],site,b['country'],None,None,b['dive_type'] or 'Buceo recreativo',note,now(),b['id']))
        db.commit()
        if os.environ.get('WORLDIVES_SEED_DEMO') == '1' and db.execute('SELECT COUNT(*) FROM travel_offers').fetchone()[0] == 0:
            offers = [
                ('Maldivas · Atolones centrales', 'Maldivas', 'Vida a bordo', '/assets/images/maldivas.webp', 'Corrientes, canales y arrecifes para una semana de inmersiones sin cambiar de base.'),
                ('Mar Rojo · Sur del Sinaí', 'Egipto', 'Viaje', '/assets/images/egipto.webp', 'Paredes, pecios y arrecifes. Una referencia clásica para planificar una escapada de buceo.'),
                ('Riviera Maya · Cenotes', 'México', 'Viaje', '/assets/images/mexico.webp', 'Cenotes y cavernas para una experiencia de buceo en agua dulce muy distinta.'),
                ('Great Barrier Reef', 'Australia', 'Vida a bordo', '/assets/images/australia.webp', 'Grandes sistemas arrecifales y vida a bordo para varios días de exploración.'),
                ('Galápagos', 'Ecuador', 'Viaje', '/assets/images/galapagos.webp', 'Un destino para buceadores que buscan fauna pelágica y condiciones cambiantes.'),
            ]
            db.executemany('INSERT INTO travel_offers(title,region,kind,image_path,summary) VALUES(?,?,?,?,?)', offers)
        db.commit()
        if os.environ.get('WORLDIVES_SEED_DEMO') == '1' and db.execute('SELECT COUNT(*) FROM reward_offers').fetchone()[0] == 0:
            offers = [
                (None, '2 € de descuento en tu próxima inmersión', 'Crédito WORLDIVES aplicable cuando el proveedor acepte esta recompensa.', 'discount', 2.0, '2 € de descuento', 'Sujeto a disponibilidad y condiciones del centro.', None),
                (None, '5 € de descuento en un curso', 'Usa tu saldo acumulado en un curso que participe en WORLDIVES.', 'course_discount', 5.0, '5 € de descuento', 'El centro debe aceptar esta recompensa.', None),
                (None, 'Seguro de día', 'Canjea saldo por un seguro de día cuando el proveedor ofrezca esta recompensa.', 'day_insurance', 5.0, 'Seguro de día', 'Sujeto a condiciones del proveedor y cobertura disponible.', None),
                (None, '10 € para una inmersión', 'Una pequeña ayuda del monedero para seguir buceando.', 'dive_credit', 10.0, '10 € de crédito', 'Solo en centros/experiencias que acepten el crédito.', None),
            ]
            db.executemany('INSERT INTO reward_offers(center_id,title,description,reward_type,cost_wallet,value_text,conditions,stock,active,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,1,?,?)', [(a,b,c,d,e,f,g,h,now(),now()) for a,b,c,d,e,f,g,h in offers])
        db.execute("UPDATE reward_offers SET active=0 WHERE center_id IS NULL")
        db.commit()
        migrate_v50_31(db)
        db.commit()
        migrate_v50_32(db)
        db.commit()
        migrate_v50_33(db)
        db.commit()
        migrate_v50_34(db)
        db.commit()


def add_columns(db, table, cols):
    have = {r['name'] for r in db.execute(f'PRAGMA table_info({table})').fetchall()}
    for name, typ in cols:
        if name not in have: db.execute(f'ALTER TABLE {table} ADD COLUMN {name} {typ}')


def backup_database(db, tag):
    """A full copy of the database before a migration that rebuilds a table (migrations add and transform; they
    never remove data without a previous copy). Kept in WOD_BACKUP_DIR (data/backups by default)."""
    folder = Path(os.environ.get('WOD_BACKUP_DIR') or (DB_PATH.parent / 'backups'))
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f'{DB_PATH.stem}-antes-{tag}-{datetime.now().strftime("%Y%m%d-%H%M%S")}.sqlite3'
    db.commit()
    dst = sqlite3.connect(target)
    try: db.backup(dst)
    finally: dst.close()
    try: os.chmod(target, 0o600)
    except OSError: pass
    return target


def migration_done(db, version):
    db.execute('CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL, backup_path TEXT, notes TEXT)')
    return bool(db.execute('SELECT 1 FROM schema_migrations WHERE version=?', (version,)).fetchone())


def rebuild_table(db, table, edit_sql):
    """SQLite cannot change a column constraint in place: the table is rebuilt with the same columns and data
    (official 12-step procedure), keeping its indexes and triggers. edit_sql(create_sql) returns the new CREATE."""
    row = db.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
    new_sql = edit_sql(row['sql'])
    if new_sql == row['sql']: return False
    extras = [r['sql'] for r in db.execute("SELECT sql FROM sqlite_master WHERE tbl_name=? AND type IN ('index','trigger') AND sql IS NOT NULL", (table,)).fetchall()]
    cols = ','.join(r['name'] for r in db.execute(f'PRAGMA table_info({table})').fetchall())
    db.commit()
    db.execute('PRAGMA foreign_keys=OFF')
    try:
        db.execute('BEGIN')
        db.execute(re.sub(r'^CREATE TABLE\s+(IF NOT EXISTS\s+)?"?' + table + r'"?', f'CREATE TABLE {table}__new', new_sql, count=1))
        db.execute(f'INSERT INTO {table}__new({cols}) SELECT {cols} FROM {table}')
        db.execute(f'DROP TABLE {table}')
        db.execute(f'ALTER TABLE {table}__new RENAME TO {table}')
        for sql in extras: db.execute(sql)
        bad = db.execute('PRAGMA foreign_key_check').fetchall()
        if bad: raise RuntimeError(f'{table}: comprobación de claves ajenas con {len(bad)} errores')
        db.execute('COMMIT')
    except Exception:
        db.execute('ROLLBACK'); raise
    finally:
        db.execute('PRAGMA foreign_keys=ON')
    return True


def migrate_v50_34(db):
    """v50.34 (Fase 2, payments aligned with the owner's decisions).
    - No commission: platform_fee stays only as history of old orders.
    - Direct charges on the provider's connected account (charge_type 'direct'; old orders keep 'destination').
    - Refund history (several partial refunds), deposits, cancellation policy per centre and per service.
    - Freelance professionals without a centre take bookings and payments with their own Stripe account:
      bookings.center_id becomes optional and bookings.provider_user_id says who provides the service.
    - Provider fiscal data for the booking voucher. Sponsorship register."""
    first = not migration_done(db, '50.34')
    backup = None
    info = {r['name']: r for r in db.execute('PRAGMA table_info(bookings)').fetchall()}
    if info['center_id']['notnull']:
        if db.execute('SELECT 1 FROM bookings LIMIT 1').fetchone(): backup = backup_database(db, 'v50_34')
        rebuild_table(db, 'bookings', lambda sql: re.sub(r'center_id INTEGER NOT NULL', 'center_id INTEGER', sql, count=1))
    add_columns(db, 'bookings', [('provider_user_id', 'INTEGER'), ('deposit_amount', 'REAL'), ('amount_paid', 'REAL DEFAULT 0'), ('amount_due', 'REAL'),
                                 ('refunded_total', 'REAL DEFAULT 0'), ('refund_proposed', 'REAL'), ('refund_status', 'TEXT'), ('refund_proposed_at', 'TEXT'),
                                 ('refund_reminded_at', 'TEXT'), ('cancel_free_hours', 'INTEGER'), ('cancel_refund_pct', 'INTEGER')])
    db.execute('CREATE INDEX IF NOT EXISTS idx_bookings_provider ON bookings(provider_user_id, booking_date, status)')
    db.execute('UPDATE bookings SET provider_user_id=(SELECT provider_user_id FROM provider_services s WHERE s.id=bookings.service_id) WHERE provider_user_id IS NULL AND service_id IS NOT NULL')
    db.execute("UPDATE bookings SET amount_paid=COALESCE(price,0) WHERE payment_status='paid' AND COALESCE(amount_paid,0)=0")
    add_columns(db, 'payment_orders', [('charge_type', 'TEXT'), ('payment_intent_id', 'TEXT'), ('payment_kind', "TEXT DEFAULT 'full'"), ('refunded_total', 'REAL DEFAULT 0'),
                                       ('incident', 'TEXT'), ('incident_note', 'TEXT'), ('incident_at', 'TEXT'), ('incident_by', 'INTEGER'), ('payee_type', 'TEXT'), ('payee_id', 'INTEGER')])
    db.execute("UPDATE payment_orders SET charge_type='destination' WHERE charge_type IS NULL")
    db.execute("UPDATE payment_orders SET refunded_total=COALESCE(refund_amount,0) WHERE status IN ('refunded','partially_refunded') AND COALESCE(refunded_total,0)=0")
    db.execute('CREATE INDEX IF NOT EXISTS idx_payment_orders_intent ON payment_orders(payment_intent_id)')
    db.execute("CREATE TABLE IF NOT EXISTS payment_refunds (id INTEGER PRIMARY KEY AUTOINCREMENT, payment_order_id INTEGER NOT NULL, booking_id INTEGER, "
               "experience_booking_id INTEGER, amount REAL NOT NULL, currency TEXT NOT NULL, reason TEXT, note TEXT, stripe_refund_id TEXT UNIQUE, status TEXT NOT NULL, "
               "source TEXT NOT NULL, created_by INTEGER, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)")
    db.execute('CREATE INDEX IF NOT EXISTS idx_payment_refunds_order ON payment_refunds(payment_order_id)')
    # The old single-refund columns become the first line of the history.
    db.execute("INSERT INTO payment_refunds(payment_order_id,booking_id,experience_booking_id,amount,currency,reason,stripe_refund_id,status,source,created_at,updated_at) "
               "SELECT id,booking_id,experience_booking_id,refund_amount,COALESCE(currency,'EUR'),'migrated',refund_id,'succeeded','migration',COALESCE(refunded_at,updated_at),COALESCE(refunded_at,updated_at) "
               "FROM payment_orders WHERE refund_amount>0 AND status IN ('refunded','partially_refunded') "
               "AND NOT EXISTS (SELECT 1 FROM payment_refunds r WHERE r.payment_order_id=payment_orders.id)")
    add_columns(db, 'users', [('stripe_account_id', 'TEXT'), ('stripe_charges_enabled', 'INTEGER DEFAULT 0'), ('stripe_payouts_enabled', 'INTEGER DEFAULT 0'),
                              ('stripe_details_submitted', 'INTEGER DEFAULT 0'), ('payments_warning_at', 'TEXT'), ('legal_name', 'TEXT'), ('tax_id', 'TEXT'),
                              ('fiscal_address', 'TEXT'), ('cancel_free_hours', 'INTEGER'), ('cancel_refund_pct', 'INTEGER'), ('cancellation_note', 'TEXT')])
    add_columns(db, 'centers', [('legal_name', 'TEXT'), ('tax_id', 'TEXT'), ('fiscal_address', 'TEXT'), ('cancel_free_hours', 'INTEGER'), ('cancel_refund_pct', 'INTEGER')])
    add_columns(db, 'provider_services', [('deposit_type', "TEXT DEFAULT 'none'"), ('deposit_value', 'REAL'), ('cancel_free_hours', 'INTEGER'), ('cancel_refund_pct', 'INTEGER')])
    add_columns(db, 'experience_bookings', [('payment_status', 'TEXT'), ('amount_paid', 'REAL DEFAULT 0'), ('refunded_total', 'REAL DEFAULT 0')])
    # Cancellation policy as numbers (free until X hours, % refunded after). The three old presets keep their meaning.
    for key, hours in CANCEL_POLICIES.items():
        db.execute('UPDATE centers SET cancel_free_hours=?,cancel_refund_pct=COALESCE(cancel_refund_pct,0) WHERE cancellation_policy=? AND cancel_free_hours IS NULL', (hours, key))
    db.execute("CREATE TABLE IF NOT EXISTS sponsorships (id INTEGER PRIMARY KEY AUTOINCREMENT, placement TEXT NOT NULL, ref_id INTEGER, sponsor_name TEXT NOT NULL, "
               "sponsor_center_id INTEGER, sponsor_contact TEXT, starts_on TEXT, ends_on TEXT, amount REAL, currency TEXT, notes TEXT, created_by INTEGER, "
               "created_at TEXT NOT NULL, ended_at TEXT)")
    db.execute('CREATE INDEX IF NOT EXISTS idx_sponsorships_ref ON sponsorships(placement, ref_id)')
    if first:
        db.execute('INSERT INTO schema_migrations(version,applied_at,backup_path,notes) VALUES(?,?,?,?)',
                   ('50.34', now(), str(backup) if backup else None, 'Fase 2: cargos directos, devoluciones, señal, política por servicio, freelance con cobros'))


def migrate_v50_33(db):
    """v50.33 (Fase 1D): 10 languages. Users of retired languages move to English (ja, ko) or simplified Chinese (zt);
    the same for emails still waiting in the queue."""
    for old, new in (('ja', 'en'), ('ko', 'en'), ('zt', 'zh')):
        db.execute('UPDATE user_profiles SET preferred_language=? WHERE preferred_language=?', (new, old))
        db.execute("UPDATE email_outbox SET lang=? WHERE lang=? AND status IN ('queued','sending')", (new, old))


def migrate_v50_32(db):
    """v50.32 (Fase 1B, booking modes). «Reserva inmediata» disappears: services and templates move to «Pago al reservar»
    (price > 0 and online payments active) or «Bajo petición» (everything else). Every change is listed in
    booking_mode_migration so the owner can review it. Old 'pending' bookings move to the new states."""
    add_columns(db, 'provider_services', [('response_hours', 'INTEGER DEFAULT 24'), ('payment_hours', 'INTEGER DEFAULT 24')])
    add_columns(db, 'service_templates', [('response_hours', 'INTEGER'), ('payment_hours', 'INTEGER')])
    add_columns(db, 'bookings', [('booking_mode', 'TEXT'), ('response_deadline', 'TEXT'), ('payment_deadline', 'TEXT'), ('hold_expires_at', 'TEXT'),
                                 ('accepted_at', 'TEXT'), ('decided_by', 'INTEGER'), ('reject_reason', 'TEXT'), ('expired_reason', 'TEXT'), ('confirmed_at', 'TEXT')])
    add_columns(db, 'centers', [('payments_warning_at', 'TEXT')])
    db.execute('''CREATE TABLE IF NOT EXISTS booking_mode_migration (id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, item_id INTEGER NOT NULL,
                  title TEXT, provider TEXT, old_mode TEXT, new_mode TEXT, reason TEXT, created_at TEXT NOT NULL)''')
    db.execute('CREATE INDEX IF NOT EXISTS idx_bookings_deadlines ON bookings(status, response_deadline, payment_deadline, hold_expires_at)')
    db.execute('''CREATE TRIGGER IF NOT EXISTS trg_bookings_mode AFTER INSERT ON bookings WHEN NEW.booking_mode IS NULL
                  BEGIN UPDATE bookings SET booking_mode='request' WHERE id=NEW.id; END''')
    for s in db.execute('''SELECT s.id,s.title,s.price,s.booking_mode,s.center_id,s.provider_user_id,COALESCE(c.name,u.fullname) AS provider_name
                             FROM provider_services s LEFT JOIN centers c ON c.id=s.center_id LEFT JOIN users u ON u.id=s.provider_user_id
                            WHERE s.booking_mode NOT IN ('payment','request') OR s.booking_mode IS NULL''').fetchall():
        price, _, _ = effective_service_tariff(db, s['id'])
        ready = service_payments_ready(db, s)
        new = 'payment' if price > 0 and ready else 'request'
        why = 'precio > 0 y cobros online activos' if new == 'payment' else ('sin precio' if price <= 0 else 'sin cobros online activos')
        db.execute('UPDATE provider_services SET booking_mode=?,updated_at=? WHERE id=?', (new, now(), s['id']))
        db.execute('INSERT INTO booking_mode_migration(kind,item_id,title,provider,old_mode,new_mode,reason,created_at) VALUES(?,?,?,?,?,?,?,?)',
                   ('service', s['id'], s['title'], s['provider_name'], s['booking_mode'], new, why, now()))
    for t in db.execute("SELECT t.*,u.center_id AS user_center,u.fullname FROM service_templates t JOIN users u ON u.id=t.provider_user_id WHERE t.booking_mode NOT IN ('payment','request') OR t.booking_mode IS NULL").fetchall():
        ready = service_payments_ready(db, {'center_id': t['user_center'], 'provider_user_id': t['provider_user_id']})
        new = 'payment' if float(t['price'] or 0) > 0 and ready else 'request'
        db.execute('UPDATE service_templates SET booking_mode=?,updated_at=? WHERE id=?', (new, now(), t['id']))
        db.execute('INSERT INTO booking_mode_migration(kind,item_id,title,provider,old_mode,new_mode,reason,created_at) VALUES(?,?,?,?,?,?,?,?)',
                   ('template', t['id'], t['name'], t['fullname'], t['booking_mode'], new, 'plantilla', now()))
    # Bookings: give every booking its mode, then translate the old 'pending' state.
    db.execute('''UPDATE bookings SET booking_mode=COALESCE((SELECT CASE WHEN s.booking_mode='payment' THEN 'payment' ELSE 'request' END FROM provider_services s WHERE s.id=bookings.service_id),'request')
                  WHERE booking_mode IS NULL''')
    for b in db.execute("SELECT * FROM bookings WHERE status='pending'").fetchall():
        open_order = db.execute("SELECT 1 FROM payment_orders WHERE booking_id=? AND status='pending'", (b['id'],)).fetchone()
        if b['payment_status'] == 'paid': new = 'confirmed'
        elif b['booking_mode'] == 'payment': new = 'payment_in_progress' if open_order else 'expired'
        else: new = 'requested'
        db.execute('UPDATE bookings SET status=?,expired_reason=CASE WHEN ?=\'expired\' THEN \'legacy_unpaid\' ELSE expired_reason END,updated_at=? WHERE id=?', (new, new, now(), b['id']))
        if new == 'expired' and b['slot_reserved']: release_booking_spots(db, b)
    # Accepted requests that still had to be paid online.
    db.execute("UPDATE bookings SET status='accepted_pending_payment' WHERE status='confirmed' AND booking_mode='request' AND payment_status IN ('required','pending')")
    db.execute("UPDATE bookings SET hold_expires_at=? WHERE status='payment_in_progress' AND hold_expires_at IS NULL", (local_iso(local_now() + _timedelta(minutes=HOLD_MINUTES)),))
    db.execute("UPDATE bookings SET payment_deadline=? WHERE status='accepted_pending_payment' AND payment_deadline IS NULL", (local_iso(local_now() + _timedelta(hours=24)),))
    db.execute("UPDATE bookings SET response_deadline=? WHERE status='requested' AND response_deadline IS NULL AND COALESCE(source,'online')='online'", (local_iso(local_now() + _timedelta(hours=24)),))


def migrate_v50_31(db):
    """v50.31 (security, Fase 1). Only adds tables/columns and moves data; nothing is deleted without a copy,
    except medical certificates (G6), which must not be kept: their files are removed and the owner is told."""
    add_columns(db, 'users', [('guest_center_id', 'INTEGER'), ('guest_email', 'TEXT'), ('email_verified_at', 'TEXT'),
                              ('marketing_consent', 'INTEGER DEFAULT 0'), ('marketing_consent_at', 'TEXT'), ('marketing_token', 'TEXT'),
                              ('totp_secret', 'TEXT'), ('totp_enabled', 'INTEGER DEFAULT 0'), ('totp_pending_secret', 'TEXT'), ('totp_recovery', 'TEXT')])
    add_columns(db, 'bookings', [('public_token', 'TEXT'), ('contact_email', 'TEXT'), ('contact_name', 'TEXT')])
    add_columns(db, 'messages', [('kind', "TEXT DEFAULT 'system'"), ('contact_phone', 'TEXT'), ('contact_email', 'TEXT'), ('sender_name', 'TEXT')])
    add_columns(db, 'center_claims', [('requested_role', "TEXT DEFAULT 'center'"), ('suggested_center_id', 'INTEGER'), ('verification_method', 'TEXT'),
                                      ('verification_note', 'TEXT'), ('email', 'TEXT')])
    db.executescript('''
      CREATE TABLE IF NOT EXISTS data_shares (user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, center_id INTEGER NOT NULL REFERENCES centers(id) ON DELETE CASCADE,
        source TEXT, granted_at TEXT NOT NULL, revoked_at TEXT, PRIMARY KEY(user_id, center_id));
      CREATE INDEX IF NOT EXISTS idx_data_shares_center ON data_shares(center_id);
      CREATE TABLE IF NOT EXISTS legal_acceptances (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        document TEXT NOT NULL, version TEXT NOT NULL, accepted_at TEXT NOT NULL, ip_hash TEXT);
      CREATE INDEX IF NOT EXISTS idx_legal_acceptances_user ON legal_acceptances(user_id, document, version);
      CREATE TABLE IF NOT EXISTS consent_log (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER REFERENCES users(id) ON DELETE CASCADE, kind TEXT NOT NULL,
        granted INTEGER NOT NULL, created_at TEXT NOT NULL, ip_hash TEXT);
      CREATE TABLE IF NOT EXISTS email_verifications (token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        email TEXT NOT NULL, expires_at TEXT NOT NULL, used_at TEXT, created_at TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS center_members (center_id INTEGER NOT NULL REFERENCES centers(id) ON DELETE CASCADE, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        member_role TEXT NOT NULL DEFAULT 'owner', created_at TEXT NOT NULL, created_by INTEGER, PRIMARY KEY(center_id, user_id));
      CREATE TABLE IF NOT EXISTS pro_invites (id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT NOT NULL UNIQUE, note TEXT, created_by INTEGER, created_at TEXT NOT NULL,
        expires_at TEXT, used_at TEXT);
    ''')
    db.execute('CREATE INDEX IF NOT EXISTS idx_users_guest ON users(guest_center_id, guest_email)')
    # Any booking created by any path gets its random token at once (24 random bytes from SQLite's CSPRNG).
    db.execute('''CREATE TRIGGER IF NOT EXISTS trg_bookings_public_token AFTER INSERT ON bookings WHEN NEW.public_token IS NULL
                  BEGIN UPDATE bookings SET public_token=lower(hex(randomblob(24))) WHERE id=NEW.id; END''')
    db.execute('CREATE INDEX IF NOT EXISTS idx_messages_booking ON messages(booking_id)')
    # Every booking gets its own long random token for the public check page (G4).
    for row in db.execute('SELECT id FROM bookings WHERE public_token IS NULL').fetchall():
        db.execute('UPDATE bookings SET public_token=? WHERE id=?', (wsec.random_token(), row['id']))
    # Existing centre managers become owners of their centre (team roles, Fase 6).
    db.execute("INSERT OR IGNORE INTO center_members(center_id,user_id,member_role,created_at) SELECT center_id,id,'owner',? FROM users WHERE role='center' AND center_id IS NOT NULL", (now(),))
    # Claims whose account no longer exists are closed (they had no cascade).
    db.execute("UPDATE center_claims SET status='orphaned' WHERE status='pending' AND user_id NOT IN (SELECT id FROM users)")
    # G6: medical certificates must not be stored. Remove any that exist and tell their owners.
    medical = db.execute('SELECT id,user_id,file_path,original_name FROM user_documents').fetchall()
    for d in medical:
        dtype = db.execute('SELECT document_type,title FROM user_documents WHERE id=?', (d['id'],)).fetchone()
        txt = fold_text(f"{dtype['document_type']} {dtype['title']}")
        if not any(w in txt for w in ('medic', 'salud')): continue
        delete_document_file(d['file_path'])
        db.execute('DELETE FROM user_documents WHERE id=?', (d['id'],))
        db.execute("DELETE FROM reward_events WHERE user_id=? AND event_key='document:certificado médico'", (d['user_id'],))
        audit(db, None, 'medical_document_removed', 'user_document', d['id'], {'owner': d['user_id']})
        try: notify_user(db, d['user_id'], 'medical_document_removed', {'document': d['original_name'] or ''}, ('user', d['user_id']))
        except Exception: pass


def hash_password(password: str) -> str:
    return wsec.hash_password(password)


def verify_password(password: str, stored: str) -> bool:
    return wsec.verify_password(password, stored)


def check_new_password(password: str):
    problem = wsec.password_problem(password)
    if problem: raise ValueError(problem)


def audit(db, user_id, action, entity_type=None, entity_id=None, details=None):
    db.execute('INSERT INTO audit_log(user_id,action,entity_type,entity_id,details,created_at) VALUES(?,?,?,?,?,?)',
               (user_id, action, entity_type, entity_id, json.dumps(details, ensure_ascii=False) if details else None, now()))


def clean_text(value, max_len=5000):
    if value is None:
        return None
    return str(value).strip()[:max_len]


class BodyTooLarge(ValueError):
    pass


def body_length(handler, limit):
    """Content-Length checked BEFORE reading anything (G7). Bodies above the limit are never read into memory."""
    raw = handler.headers.get('Content-Length', '0') or '0'
    try: length = int(raw)
    except ValueError: raise ValueError('Cabecera Content-Length no válida.')
    if length < 0: raise ValueError('Cabecera Content-Length no válida.')
    if length > limit: raise BodyTooLarge(f'La petición supera el tamaño máximo permitido ({limit // (1024*1024) or 1} MB).')
    return length


def json_body(handler):
    """The JSON body of the request (read once and cached: several helpers may ask for it)."""
    cached = getattr(handler, '_json_cache', None)
    if cached is not None: return cached
    length = body_length(handler, MAX_BODY)
    raw = handler.rfile.read(length) if length else b''
    if not raw:
        handler._json_cache = {}; return handler._json_cache
    try: data = json.loads(raw.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError): raise ValueError('El cuerpo de la petición no es un JSON válido.')
    if not isinstance(data, dict): raise ValueError('El cuerpo de la petición debe ser un objeto JSON.')
    handler._json_cache = data
    return data


def parse_multipart(handler):
    ctype = handler.headers.get('Content-Type', '')
    if not ctype.lower().startswith('multipart/form-data'): raise ValueError('Envía el archivo como formulario (multipart/form-data).')
    length = body_length(handler, MAX_UPLOAD)
    body = handler.rfile.read(length)
    msg = BytesParser(policy=policy.default).parsebytes((f'Content-Type: {ctype}\r\nMIME-Version: 1.0\r\n\r\n').encode() + body)
    fields = {}
    files = {}
    for part in msg.iter_parts():
        name = part.get_param('name', header='content-disposition')
        if not name:
            continue
        filename = part.get_filename()
        data = part.get_payload(decode=True) or b''
        if filename is not None:
            files[name] = {'filename': Path(filename).name, 'content': data, 'content_type': part.get_content_type()}
        else:
            charset = part.get_content_charset() or 'utf-8'
            fields[name] = data.decode(charset, errors='replace')
    return fields, files


def save_upload(user_id: int, file_info: dict, prefix: str) -> str:
    """Private document (G1/G8): type checked by its first bytes, at most WOD_MAX_DOCUMENT_MB, stored outside /public.
    Returns the path relative to STORAGE (never served directly)."""
    content = file_info.get('content') or b''
    if not content: raise ValueError('El archivo está vacío.')
    if len(content) > wcfg.MAX_DOCUMENT_BYTES: raise ValueError(f'El archivo pesa demasiado. Máximo {wcfg.MAX_DOCUMENT_BYTES // (1024*1024)} MB.')
    ext = wsec.sniff_document(content)
    if not ext: raise ValueError('Formato no admitido. Usa un PDF o una imagen JPG, PNG o WEBP.')
    UPLOADS.mkdir(parents=True, exist_ok=True)
    filename = f'{prefix}_{user_id}_{secrets.token_hex(12)}{ext}'
    out = UPLOADS / filename
    out.write_bytes(content)
    try: os.chmod(out, 0o600)
    except OSError: pass
    return 'documents/' + filename


def document_file_path(stored):
    """Absolute path of a private document. Accepts the v50.31 format (documents/…) and the older storage/documents/…."""
    rel = str(stored or '').replace('\\', '/')
    if rel.startswith('storage/'): rel = rel[len('storage/'):]
    target = (STORAGE / rel).resolve()
    if not target.is_relative_to(STORAGE.resolve()): return None
    return target


def delete_document_file(stored):
    fp = document_file_path(stored)
    if fp and fp.exists():
        try: fp.unlink()
        except OSError as exc: sys.stderr.write(f'[documentos] no se pudo borrar {fp.name}: {exc}\n')


def current_user(handler, db):
    cookie = handler.headers.get('Cookie','')
    token = None
    for item in cookie.split(';'):
        k, _, v = item.strip().partition('=')
        if k == COOKIE:
            token = v
            break
    if not token:
        return None
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    session = db.execute('SELECT user_id,created_at,last_seen FROM sessions WHERE token_hash=?', (token_hash,)).fetchone()
    if not session:
        return None
    current = time.time()
    if current - session['last_seen'] > SESSION_TTL_SECONDS or current - session['created_at'] > SESSION_TTL_SECONDS:
        db.execute('DELETE FROM sessions WHERE token_hash=?', (token_hash,)); db.commit()
        return None
    # Sliding expiry, written at most once a minute per session to keep writes cheap.
    if current - session['last_seen'] > 60:
        db.execute('UPDATE sessions SET last_seen=? WHERE token_hash=?', (current, token_hash)); db.commit()
    user_id = session['user_id']
    row = db.execute('''SELECT u.*, c.name AS center_name FROM users u LEFT JOIN centers c ON c.id=u.center_id WHERE u.id=?''', (user_id,)).fetchone()
    return dict(row) if row else None


def require_user(handler, db):
    user = current_user(handler, db)
    if not user:
        raise PermissionError('Necesitas iniciar sesión.')
    return user


def require_role(user, roles):
    if user['role'] not in roles:
        raise PermissionError('No tienes permisos para realizar esta acción.')


# Bookings that no longer exist for the centre (they never give access to the diver's data).
INACTIVE_BOOKING_STATES = ('cancelled', 'rejected', 'expired', 'unpaid')


def center_can_see_user(db, center_id, user_id):
    """G1/G5: a centre sees a registered diver's profile and documents only when the diver booked with that centre
    themselves (an online booking that is still alive) or explicitly agreed to share the data (QR check-in or the
    «Compartir mis datos» switch). Bookings typed in by the centre or imported through its API never open that access."""
    if not center_id or not user_id: return False
    placeholders = ','.join('?' * len(INACTIVE_BOOKING_STATES))
    if db.execute(f"SELECT 1 FROM bookings WHERE center_id=? AND user_id=? AND COALESCE(source,'online')='online' AND status NOT IN ({placeholders}) LIMIT 1",
                  (center_id, user_id, *INACTIVE_BOOKING_STATES)).fetchone():
        return True
    return bool(db.execute('SELECT 1 FROM data_shares WHERE center_id=? AND user_id=? AND revoked_at IS NULL', (center_id, user_id)).fetchone())


def provider_can_see_user(db, b):
    """The provider of a booking sees the diver's profile: centres by center_can_see_user; a freelance professional
    without a centre only while the diver has an alive online booking of his own with him."""
    if b['center_id']: return center_can_see_user(db, b['center_id'], b['user_id'])
    prov = b['provider_user_id'] if 'provider_user_id' in b.keys() else None
    if not prov: return False
    placeholders = ','.join('?' * len(INACTIVE_BOOKING_STATES))
    return bool(db.execute(f"SELECT 1 FROM bookings WHERE center_id IS NULL AND provider_user_id=? AND user_id=? AND COALESCE(source,'online')='online' AND status NOT IN ({placeholders}) LIMIT 1",
                           (prov, b['user_id'], *INACTIVE_BOOKING_STATES)).fetchone())


VERIFICATION_METHODS = {'email_domain': 'Email del dominio del centro', 'phone_call': 'Llamada al teléfono público del centro',
                        'document': 'Documento (licencia, alta fiscal o registro)'}
MAX_DOCUMENTS_PER_USER = 30
# G6: health data (medical certificates) are never uploaded to WORLDIVES: the diver hands them to the centre.
DOCUMENT_TYPES = ('Titulación', 'Seguro', 'Documento de identidad', 'Documento adicional')
MEDICAL_WORDS = ('medic', 'médic', 'salud', 'health', 'medical')


def setup_allowed():
    """G9: the web installer (#/setup) and the «first user is admin» rule only exist with WOD_ALLOW_SETUP=1."""
    return wcfg.env_flag('WOD_ALLOW_SETUP')


def registration_open():
    """Demo deployments (WOD_DEMO_MODE=1) do not accept new accounts."""
    return not wcfg.demo_mode() and not wcfg.env_flag('WOD_REGISTRATION_CLOSED')


def pro_signup_check(db, data):
    """Pilot mode (Administración → Funciones): only invited centres and professionals can sign up."""
    row = db.execute("SELECT value FROM site_settings WHERE key='feature_pilot_mode'").fetchone()
    if not row or row['value'] != '1': return
    code = (clean_text(data.get('invite_code'), 60) or '').strip().upper()
    inv = db.execute("SELECT id FROM pro_invites WHERE code=? AND used_at IS NULL AND (expires_at IS NULL OR expires_at>=?)", (code, now()[:10])).fetchone() if code else None
    if not inv: raise PermissionError('WORLDIVES está en fase piloto: el alta de centros y profesionales es solo por invitación. Escríbenos para pedir la tuya.')
    db.execute('UPDATE pro_invites SET used_at=? WHERE id=?', (now(), inv['id']))


def normalize_lang(lang):
    """Languages of the site (v50.33): retired ones fall back (ja/ko → en, zt → zh)."""
    lang = (lang or 'es').lower()
    lang = {'ja': 'en', 'ko': 'en', 'zt': 'zh'}.get(lang, lang)
    return lang if lang in MAIL_LANGS else 'es'


def clean_url_field(value, max_len=500):
    return wsec.clean_http_url(value, max_len) if value not in (None, '') else None


def clean_lat(v):
    try: x = float(v)
    except (TypeError, ValueError): return None
    return x if -90 <= x <= 90 and x != 0 else None


def clean_lng(v):
    try: x = float(v)
    except (TypeError, ValueError): return None
    return x if -180 <= x <= 180 and x != 0 else None


def clean_date(v):
    v = (clean_text(v, 10) or '').strip()
    if not v: return None
    try: return _dt.date.fromisoformat(v).isoformat()
    except ValueError: raise ValueError('La fecha no es válida (usa el formato AAAA-MM-DD).')


def clean_document_type(v):
    v = (clean_text(v, 50) or 'Documento adicional').strip()
    if any(w in fold_text(v) for w in MEDICAL_WORDS):
        raise ValueError('No subas certificados médicos a WORLDIVES: entrégalos directamente al centro de buceo.')
    return v if v in DOCUMENT_TYPES else 'Documento adicional'


def unique_center_name(db, name, city):
    """centers has UNIQUE(name,country,city): a new draft with the same name gets a numbered suffix."""
    base = clean_text(name, 170) or 'Centro'
    cand = base; n = 2
    while db.execute('SELECT 1 FROM centers WHERE name=? AND COALESCE(city,"")=COALESCE(?,"")', (cand, city)).fetchone():
        cand = f'{base} ({n})'; n += 1
    return cand


def booking_status_label(state):
    return wbk.state_label(state)


def short_name(fullname):
    """«Laura M.»: first name and the initial of the surname (public booking check, G4)."""
    parts = [p for p in str(fullname or '').split() if p]
    if not parts: return ''
    return parts[0] + (f' {parts[1][0].upper()}.' if len(parts) > 1 else '')


def booking_check_url(db, bid, base):
    """Link printed in the QR and the PDF: it carries the booking's long random token (G4)."""
    row = db.execute('SELECT public_token FROM bookings WHERE id=?', (bid,)).fetchone()
    token = row['public_token'] if row else None
    if row and not token:
        token = wsec.random_token(); db.execute('UPDATE bookings SET public_token=? WHERE id=?', (token, bid)); db.commit()
    return f'{base}/#/verificarreserva?id={bid}&t={token}'


def qr_svg(payload, color='#000000'):
    import qrcode
    qr = qrcode.QRCode(box_size=1, border=1); qr.add_data(payload); qr.make(fit=True)
    m = qr.get_matrix(); n = len(m); sc = 8; mg = sc * 3; size = n * sc + mg * 2
    rects = ''.join(f'<rect x="{mg+c*sc}" y="{mg+r*sc}" width="{sc}" height="{sc}"/>' for r, row_ in enumerate(m) for c, v in enumerate(row_) if v)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" width="{size}" height="{size}" shape-rendering="crispEdges">'
            f'<rect width="100%" height="100%" fill="#fff"/><g fill="{html.escape(color)}">{rects}</g></svg>').encode()


def record_acceptances(db, user_id, docs, ip='', version=None):
    """Keeps WHO accepted WHICH version of WHICH legal document, WHEN and from which (pseudonymised) IP."""
    for doc in docs:
        ver = version or legal_doc_version(db, doc)
        db.execute('INSERT INTO legal_acceptances(user_id,document,version,accepted_at,ip_hash) VALUES(?,?,?,?,?)', (user_id, doc, ver, now(), wsec.ip_hash(ip) if ip else None))
    if any(d in ('terminos', 'privacidad') for d in docs):
        db.execute('UPDATE users SET terms_version=?,terms_accepted_at=? WHERE id=?', (legal_doc_version(db, 'terminos'), now(), user_id))
    if 'centros' in docs:
        db.execute('UPDATE users SET pro_terms_version=?,pro_terms_accepted_at=? WHERE id=?', (legal_doc_version(db, 'centros'), now(), user_id))


def set_marketing_consent(db, user_id, consent, ip=''):
    """Commercial emails only with explicit, separate consent; one-click unsubscribe token (Fase 4.3)."""
    db.execute('UPDATE users SET marketing_consent=?,marketing_consent_at=?,marketing_token=COALESCE(marketing_token,?) WHERE id=?',
               (1 if consent else 0, now(), wsec.random_token(18), user_id))
    db.execute('INSERT INTO consent_log(user_id,kind,granted,created_at,ip_hash) VALUES(?,?,?,?,?)', (user_id, 'marketing', 1 if consent else 0, now(), wsec.ip_hash(ip) if ip else None))


def send_email_verification(db, user_id, new_email=None):
    """Email verification at sign-up and when the email changes: a single-use link valid for 48 hours."""
    u = db.execute('SELECT id,email,fullname FROM users WHERE id=?', (user_id,)).fetchone()
    if not u: return None
    target = (new_email or u['email'] or '').lower()
    if not mail_deliverable(target): return None
    token = wsec.random_token(32)
    exp = (datetime.now(timezone.utc) + _timedelta(hours=48)).isoformat(timespec='seconds')
    db.execute('UPDATE email_verifications SET used_at=? WHERE user_id=? AND used_at IS NULL', (now(), user_id))
    db.execute('INSERT INTO email_verifications(token_hash,user_id,email,expires_at,created_at) VALUES(?,?,?,?,?)', (hashlib.sha256(token.encode()).hexdigest(), user_id, target, exp, now()))
    ctx, lang = user_mail_ctx(db, user_id)
    if ctx:
        ctx.update({'verify_url': f'{public_site_url()}/#/verificar-email?token={token}', 'new_email': target})
        queue_email(db, 'verify_email_change' if new_email else 'verify_email', target, u['fullname'], ctx, lang, ('user', user_id))
    return token


def booking_notice_recipient(db, user, booking_id, experience_booking_id):
    """G11: the notice must be about a booking of the sender's own centre (or of his own freelance services/experiences)."""
    if booking_id:
        b = db.execute('SELECT b.user_id,b.center_id,s.provider_user_id FROM bookings b LEFT JOIN provider_services s ON s.id=b.service_id WHERE b.id=?', (booking_id,)).fetchone()
        if not b: raise ValueError('Reserva no válida.')
        if user['role'] == 'center' and b['center_id'] == user['center_id']: return b['user_id']
        if user['role'] == 'freelance' and b['provider_user_id'] == user['id']: return b['user_id']
        raise PermissionError('Esta reserva no pertenece a tu centro.')
    eb = db.execute('SELECT eb.user_id,e.provider_user_id,e.center_id FROM experience_bookings eb JOIN travel_experiences e ON e.id=eb.travel_experience_id WHERE eb.id=?', (experience_booking_id,)).fetchone()
    if not eb: raise ValueError('Solicitud no válida.')
    if eb['provider_user_id'] == user['id'] or (user['role'] == 'center' and eb['center_id'] and eb['center_id'] == user['center_id']): return eb['user_id']
    raise PermissionError('Esta solicitud no es tuya.')


def provider_contact(db, user):
    """Phone and email shown under a notice: the diver answers the centre directly, not through WORLDIVES."""
    if user['role'] == 'center' and user.get('center_id'):
        c = db.execute('SELECT name,phone,email FROM centers WHERE id=?', (user['center_id'],)).fetchone()
        if c: return c['name'], c['phone'] or '', c['email'] or ''
    p = db.execute('SELECT phone FROM user_profiles WHERE user_id=?', (user['id'],)).fetchone()
    return user['fullname'], (p['phone'] if p else '') or '', user['email'] or ''


def send_booking_notice(db, user, recipient_id, booking_id, experience_booking_id, subject, body):
    name, phone, email = provider_contact(db, user)
    mid = db.execute('INSERT INTO messages(sender_user_id,recipient_user_id,booking_id,experience_booking_id,subject,body,created_at,kind,contact_phone,contact_email,sender_name) VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                     (user['id'], recipient_id, booking_id, experience_booking_id, subject, body, now(), 'notice', phone, email, name)).lastrowid
    ctx, lang = user_mail_ctx(db, recipient_id)
    to = ctx['email'] if ctx else ''
    if booking_id:
        bc = db.execute('SELECT contact_email FROM bookings WHERE id=?', (booking_id,)).fetchone()
        if not mail_deliverable(to) and bc and mail_deliverable(bc['contact_email']): to = bc['contact_email']
    if ctx and mail_deliverable(to):
        ctx.update({'provider': name, 'notice_subject': subject, 'notice_body': body, 'provider_phone': phone or '—', 'provider_email': email or '—',
                    'booking_url': f'{public_site_url()}/#/reserva?id={booking_id}' if booking_id else f'{public_site_url()}/#/area'})
        queue_email(db, 'booking_notice', to, ctx['name'], ctx, lang, ('booking', booking_id) if booking_id else ('experience_booking', experience_booking_id))
    return mid


def login_second_factor(db, user, data):
    """Two-step verification hook (Fase 4). Returns a JSON answer when a code is still needed, else None."""
    return None


def grant_data_share(db, user_id, center_id, source):
    db.execute('''INSERT INTO data_shares(user_id,center_id,source,granted_at) VALUES(?,?,?,?)
                  ON CONFLICT(user_id,center_id) DO UPDATE SET revoked_at=NULL,source=excluded.source,granted_at=excluded.granted_at''',
               (user_id, center_id, source, now()))


SERVICE_TYPES = {'inmersion','curso','salida','experiencia','vida_a_bordo','viaje','alquiler_equipo'}
BOOKING_MODES = set(wbk.MODES)  # 'payment' (Pago al reservar) and 'request' (Bajo petición); 'instant' no longer exists


def clean_booking_mode(db, user, data, price):
    """Validates the booking mode of a service. «Pago al reservar» needs online payments active (Fase 1B)."""
    mode = clean_text(data.get('booking_mode'), 30) or 'request'
    if mode == 'payment_keep':  # editing other fields of a «Pago al reservar» service while payments are off: allowed, it stays not bookable
        return 'payment', wbk.clamp_hours(data.get('response_hours'), wbk.DEFAULT_RESPONSE_HOURS), wbk.clamp_hours(data.get('payment_hours'), wbk.DEFAULT_PAYMENT_HOURS)
    if mode == 'instant': mode = 'payment' if price > 0 else 'request'
    if mode not in BOOKING_MODES: raise ValueError('Elige el modo de reserva: «Pago al reservar» o «Bajo petición».')
    if mode == 'payment' and not service_payments_ready(db, {'center_id': user['center_id'] if user['role'] == 'center' else None, 'provider_user_id': user['id']}):
        raise ValueError('Activa los cobros online para usar «Pago al reservar» (Panel → Cobros y pagos).')
    return mode, wbk.clamp_hours(data.get('response_hours'), wbk.DEFAULT_RESPONSE_HOURS), wbk.clamp_hours(data.get('payment_hours'), wbk.DEFAULT_PAYMENT_HOURS)
MAX_TEMPLATES_PER_PROVIDER = 50


def clean_service_template(data):
    """Validate a service template payload. Only fields of a service definition are kept."""
    name=clean_text(data.get('name'),80)
    if not name: raise ValueError('Ponle un nombre a la plantilla.')
    stype=clean_text(data.get('service_type'),60) or 'inmersion'
    if stype not in SERVICE_TYPES: stype='inmersion'
    mode=clean_text(data.get('booking_mode'),30) or 'request'
    if mode not in BOOKING_MODES: mode='request'
    resp=wbk.clamp_hours(data.get('response_hours'),wbk.DEFAULT_RESPONSE_HOURS); payh=wbk.clamp_hours(data.get('payment_hours'),wbk.DEFAULT_PAYMENT_HOURS)
    def pos_int(v):
        try: v=int(float(v or 0))
        except (TypeError,ValueError): return None
        return v if v>0 else None
    price=data.get('price')
    try: price=None if price in (None,'') else max(0.0,float(price))
    except (TypeError,ValueError): price=None
    color=clean_text(data.get('color'),20)
    if color and not re.fullmatch(r'#[0-9a-fA-F]{6}',color): color=None
    return {'name':name,'service_type':stype,'title':clean_text(data.get('title'),180),'description':clean_text(data.get('description'),5000),
            'duration_minutes':pos_int(data.get('duration_minutes')),'max_participants':pos_int(data.get('max_participants')),
            'booking_mode':mode,'color':color,'price':price,'response_hours':resp,'payment_hours':payh}


def effective_service_tariff(db, service_id, target_date=None):
    """Return the tariff effective for a service on target_date.
    Falls back to provider_services.price when no tariff history exists.
    """
    target = (target_date or now()[:10])[:10]
    row = db.execute('''SELECT ct.price,ct.currency,ct.effective_from
                       FROM center_tariffs ct
                       JOIN provider_services ps ON ps.id=ct.service_id
                       WHERE ct.service_id=? AND ct.center_id=ps.center_id AND ct.effective_from<=?
                       ORDER BY ct.effective_from DESC, ct.id DESC LIMIT 1''',(service_id,target)).fetchone()
    if row:
        return float(row['price'] or 0), row['currency'] or 'EUR', row['effective_from']
    row = db.execute('SELECT price,currency FROM provider_services WHERE id=?',(service_id,)).fetchone()
    return (float(row['price'] or 0), row['currency'] or 'EUR', None) if row else (0.0,'EUR',None)


def booking_quote(db, center_id, service, participants, activity_date=None, extra_ids=None, equipment_codes=None):
    """Single source of truth for what a booking costs.
    Activity, rental equipment and extras are priced per participant. Returns (total, currency, lines)."""
    participants=max(1,int(participants or 1)); lines=[]
    currency='EUR'
    if service:
        unit, currency, _ = effective_service_tariff(db, service['id'], activity_date)
        lines.append({'kind':'service','label':service['title'],'unit':round(unit,2),'qty':participants,'total':round(unit*participants,2)})
    # Rental items are 'code' (one per participant) or 'code:qty' (only some divers need it; at most one per participant).
    qty_by_code={}
    for raw in (equipment_codes or []):
        raw=clean_text(raw,48) or ''
        code,_,q=raw.partition(':')
        code=code.strip()
        if not code: continue
        try: n=int(q) if q else participants
        except ValueError: n=participants
        n=max(0,min(participants,n))
        if n: qty_by_code[code]=n
    codes=list(qty_by_code)[:40]
    if codes:
        rows=db.execute('SELECT code,label,price FROM center_equipment WHERE center_id=? AND active=1 AND price IS NOT NULL AND code IN (%s) ORDER BY sort_order' % ','.join('?'*len(codes)),[center_id]+codes).fetchall()
        for r in rows:
            n=qty_by_code[r['code']]; unit=float(r['price'] or 0); lines.append({'kind':'equipment','code':r['code'],'label':r['label'],'unit':round(unit,2),'qty':n,'total':round(unit*n,2)})
    ids=[]
    for x in (extra_ids or []):
        try: ids.append(int(x))
        except (TypeError,ValueError): pass
    if ids:
        rows=db.execute('SELECT id,name,price FROM center_extras WHERE center_id=? AND active=1 AND id IN (%s) ORDER BY name' % ','.join('?'*len(ids)),[center_id]+ids).fetchall()
        for r in rows:
            unit=float(r['price'] or 0); lines.append({'kind':'extra','id':r['id'],'label':r['name'],'unit':round(unit,2),'qty':participants,'total':round(unit*participants,2)})
    total=round(sum(l['total'] for l in lines),2)
    return total, currency, lines


def as_list(value):
    if value is None: return []
    if isinstance(value,(list,tuple)): return list(value)
    return [v for v in str(value).split(',') if v.strip()]


def reserve_slot_spots(db, slot_id, qty):
    """Atomically take qty spots from a departure. Returns False when there are not enough."""
    return db.execute("UPDATE service_slots SET spots_available=spots_available-?,status=CASE WHEN spots_available-?<=0 THEN 'full' ELSE 'open' END,updated_at=? WHERE id=? AND status IN ('open','full') AND spots_available>=?",(qty,qty,now(),slot_id,qty)).rowcount==1


def release_slot_spots(db, slot_id, qty):
    db.execute("UPDATE service_slots SET spots_available=MIN(spots_total,spots_available+?),status=CASE WHEN status='closed' THEN 'closed' ELSE 'open' END,updated_at=? WHERE id=?",(qty,now(),slot_id))


def find_or_create_customer(db, fullname, email, phone, center_id=None):
    """G5: a booking typed in by a centre (or imported through its API) is NEVER linked to a registered account,
    not even when the email matches. It gets the centre's own customer record (a login-less user, password '!',
    tied to that centre by guest_center_id). The real email and phone travel with the booking (contact_email /
    contact_phone) so the confirmation still reaches the customer. If that person has an account, the centre
    only sees it once the person books by himself or accepts to share his data."""
    email=(clean_text(email,160) or '').lower()
    if email and center_id:
        row=db.execute("SELECT id FROM users WHERE guest_center_id=? AND password_hash='!' AND lower(guest_email)=? LIMIT 1",(center_id,email)).fetchone()
        if row: return row['id']
    placeholder=f'cliente-{secrets.token_hex(8)}@sin-email.worldives.local'
    uid=db.execute('INSERT INTO users(fullname,email,username,password_hash,role,created_at,guest_center_id,guest_email) VALUES(?,?,?,?,?,?,?,?)',
                   (clean_text(fullname,180) or 'Cliente',placeholder,'cliente_'+secrets.token_hex(6),'!','recreational',now(),center_id,email or None)).lastrowid
    db.execute('INSERT OR IGNORE INTO user_profiles(user_id,phone,updated_at) VALUES(?,?,?)',(uid,clean_text(phone,60),now()))
    return uid


def is_guest_user(db, user_id):
    """A customer record without login created by a centre: its data was typed by that centre."""
    r = db.execute('SELECT password_hash, guest_center_id FROM users WHERE id=?', (user_id,)).fetchone()
    return bool(r and r['password_hash'] == '!' and r['guest_center_id'])


def resolve_travel_offer(db, data):
    """Destination for an experience: an existing one or a new one created by the provider."""
    tid=int(data.get('travel_offer_id') or 0)
    if tid:
        if not db.execute('SELECT 1 FROM travel_offers WHERE id=? AND active=1',(tid,)).fetchone(): raise ValueError('Destino no válido.')
        return tid
    title=clean_text(data.get('new_destination'),180)
    if not title: return 0
    same=db.execute('SELECT id FROM travel_offers WHERE lower(title)=lower(?) AND active=1',(title,)).fetchone()
    if same: return same['id']
    return db.execute('INSERT INTO travel_offers(title,region,kind,image_path,summary,description,active) VALUES(?,?,?,?,?,?,1)',(title,clean_text(data.get('new_destination_region'),100) or title,'Viaje',None,'','')).lastrowid


def sync_service_experience(db, user, service_id, data):
    """Publish (or unpublish) a service as an Experience. The service stays the single source of truth
    for title, description, price and departures; the experience only places it in a destination."""
    svc=db.execute('SELECT * FROM provider_services WHERE id=?',(service_id,)).fetchone()
    if not svc: return
    existing=db.execute('SELECT * FROM travel_experiences WHERE service_id=?',(service_id,)).fetchone()
    publish=bool(data.get('publish_experience'))
    if not publish:
        if existing: db.execute('UPDATE travel_experiences SET active=0,updated_at=? WHERE id=?',(now(),existing['id']))
        return
    tid=resolve_travel_offer(db,data) or (existing['travel_offer_id'] if existing else 0)
    if not tid: raise ValueError('Elige el destino donde aparecerá la experiencia.')
    status='published' if user['role'] in {'center','admin'} else (existing['status'] if existing and existing['status']=='published' else 'pending')
    price,currency,_=effective_service_tariff(db,service_id)
    summary=(svc['description'] or '')[:300]
    if existing:
        db.execute('UPDATE travel_experiences SET travel_offer_id=?,title=?,summary=?,description=?,price=?,currency=?,status=?,active=1,updated_at=? WHERE id=?',(tid,svc['title'],summary,svc['description'],price,currency,status,now(),existing['id']))
    else:
        db.execute('INSERT INTO travel_experiences(travel_offer_id,title,provider_user_id,center_id,provider_type,summary,description,price,currency,status,active,service_id,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                   (tid,svc['title'],user['id'],svc['center_id'],'center' if user['role']=='center' else 'freelance',summary,svc['description'],price,currency,status,1,service_id,now(),now()))


def enrich_experiences(db, rows):
    """Experiences linked to a service show live price and upcoming departures from that service."""
    out=[]
    for r in rows:
        d=dict(r)
        if d.get('service_id'):
            price,currency,_=effective_service_tariff(db,d['service_id'])
            d['price']=price; d['currency']=currency
            slots=db.execute("SELECT id,slot_date,slot_time,spots_total,spots_available FROM service_slots WHERE service_id=? AND status IN ('open','full') AND slot_date>=date('now') ORDER BY slot_date,slot_time LIMIT 12",(d['service_id'],)).fetchall()
            d['departures']=[dict(x) for x in slots]
            if slots:
                d['start_date']=slots[0]['slot_date']; d['spots_available']=slots[0]['spots_available']; d['spots_total']=slots[0]['spots_total']
            d['book_url']=f"#/reservar?center={d.get('center_id') or ''}&service={d['service_id']}"
        out.append(d)
    return out


IMAGE_SIGNATURES = {b'\xff\xd8\xff': '.jpg', b'\x89PNG\r\n\x1a\n': '.png'}
MAX_IMAGE_BYTES = 6 * 1024 * 1024
MAX_GALLERY_IMAGES = 12


def save_public_image(file_info, prefix):
    """Store an uploaded image under /assets/uploads after checking it really is a JPG, PNG or WEBP."""
    if not file_info: raise ValueError('Adjunta una imagen.')
    content=file_info.get('content') or b''
    if len(content)>MAX_IMAGE_BYTES: raise ValueError('La imagen pesa demasiado. Máximo 6 MB.')
    ext=None
    for sig,e in IMAGE_SIGNATURES.items():
        if content.startswith(sig): ext=e
    if content[:4]==b'RIFF' and content[8:12]==b'WEBP': ext='.webp'
    if not ext: raise ValueError('Formato no admitido. Usa una foto JPG, PNG o WEBP.')
    PHOTOS.mkdir(parents=True,exist_ok=True)
    name=f'{prefix}_{secrets.token_hex(8)}{ext}'
    (PHOTOS/name).write_bytes(content)
    return '/assets/uploads/'+name


def delete_public_image(url):
    """Remove a file previously stored by save_public_image (never anything outside /assets/uploads)."""
    if not url or not str(url).startswith('/assets/uploads/'): return
    target=(PHOTOS/str(url)[len('/assets/uploads/'):]).resolve()
    if str(target).startswith(str(PHOTOS.resolve())) and target.exists():
        try: target.unlink()
        except OSError: pass


VIRTUAL_TYPES = {'panorama', 'video360', 'streetview', 'external360'}


def virtual_public_row(row):
    """G3: a stored link is only handed to browsers when it is an allowed https embed (older rows are re-checked)."""
    d = dict(row)
    if d.get('url') and not wsec.embed_allowed(d['url']): d['url'] = None; d['url_blocked'] = True
    if d.get('media_path') and not str(d['media_path']).startswith('/assets/uploads/virtual/'): d['media_path'] = None
    return d


def can_manage_virtual(db, user, pid):
    row = db.execute('SELECT center_id FROM dive_points WHERE id=?', (pid,)).fetchone()
    if not row: raise ValueError('Punto no encontrado.')
    if user['role'] == 'center' and row['center_id'] != user['center_id']:
        raise PermissionError('No puedes gestionar el recorrido virtual de este punto.')
    return row


def clean_virtual_payload(data, has_file=False):
    """Validates a virtual tour (server side; the browser checks the same rules). The URL must be https:// on one of
    the providers in WOD_EMBED_DOMAINS (youtube-nocookie.com, player.vimeo.com, google.com/maps by default)."""
    etype = clean_text(data.get('experience_type'), 40) or 'panorama'
    if etype not in VIRTUAL_TYPES: raise ValueError('Tipo de experiencia no válido.')
    url = wsec.clean_embed_url(clean_text(data.get('url'), 1000))
    if etype in {'video360', 'streetview', 'external360'} and not url and not has_file:
        raise ValueError('Añade una URL o un archivo para esta experiencia.')
    try: duration = int(data.get('duration_seconds') or 0) or None
    except (TypeError, ValueError): duration = None
    if duration is not None and not 0 < duration < 24 * 3600: duration = None
    return {'type': etype, 'url': url, 'title': clean_text(data.get('title'), 180) or 'Recorrido virtual',
            'provider': clean_text(data.get('provider'), 100), 'description': clean_text(data.get('description'), 2000), 'duration': duration}


def save_virtual_media(file_info, pid, etype):
    """Panorama images or 360° videos for a dive site: type checked by content and size limited (WOD_MAX_VIRTUAL_UPLOAD_MB)."""
    content = file_info.get('content') or b''
    if len(content) > wcfg.MAX_VIRTUAL_UPLOAD_BYTES:
        raise ValueError(f'El archivo pesa demasiado. Máximo {wcfg.MAX_VIRTUAL_UPLOAD_BYTES // (1024*1024)} MB.')
    image = wsec.sniff_document(content); video = wsec.sniff_video(content)
    if image == '.pdf': image = None
    ext = image if etype == 'panorama' else video if etype == 'video360' else (image or video)
    if not ext: raise ValueError('Formato no admitido para este tipo de recorrido.')
    folder = PHOTOS / 'virtual'; folder.mkdir(parents=True, exist_ok=True)
    out = folder / f'virtual_{pid}_{secrets.token_hex(8)}{ext}'
    out.write_bytes(content)
    return '/assets/uploads/virtual/' + out.name


def center_gallery(row):
    try: items=json.loads(row['gallery_json'] or '[]') if row and 'gallery_json' in row.keys() else []
    except (TypeError,ValueError): items=[]
    return [x for x in items if isinstance(x,str) and x.startswith('/assets/')][:MAX_GALLERY_IMAGES]


def point_row(row):
    if not row:
        return None
    d = dict(row)
    # Provenance metadata is kept internally but is not exposed in the public catalog API.
    for k in ('source_name', 'source_url', 'data_confidence'):
        d.pop(k, None)
    return d


def center_row(row):
    if not row:
        return None
    d = dict(row)
    # Provenance metadata is kept internally but is not exposed in the public catalog API.
    for k in ('source_name', 'source_url', 'logo_source', 'data_confidence', 'stripe_account_id', 'stripe_details_submitted', 'stripe_payouts_enabled'):
        d.pop(k, None)
    if 'gallery_json' in d:
        d['gallery']=center_gallery(row); d.pop('gallery_json',None)
    d['online_payments']=bool(d.pop('stripe_charges_enabled',0)) and bool(stripe_secret()) and bool(row['stripe_payouts_enabled'] if 'stripe_payouts_enabled' in row.keys() else 0)
    return d




# ---------------------------------------------------------------------------
# Dive types: one definition shared by the «Tipos de buceo» pages and the points filter.
# `match` lists accent-free fragments searched in the folded dive_type (and name/description when noted).
# ---------------------------------------------------------------------------
DIVE_CATEGORIES = [
    {'slug':'arrecifes','label':'Arrecifes','depth':(5,25),'level':'Todos los niveles','cert':'Open Water','tone':'reef',
     'summary':'Fondos coralinos o rocosos llenos de vida, ideales para empezar y para volver siempre.',
     'body':'El arrecife es la inmersión más versátil: fondos rocosos o de coral con peces de colores, nudibranquios, morenas y gorgonias. Se adapta a todos los niveles porque suele permitir elegir la profundidad.',
     'need':'Certificación básica. Flotabilidad controlada para no tocar el fondo.',
     'tip':'Las mañanas suelen tener mejor visibilidad y menos oleaje.',
     'where':"(fold(p.dive_type) LIKE '%arrecif%' AND fold(p.dive_type) NOT LIKE '%pecio%')"},
    {'slug':'paredes','label':'Paredes','depth':(10,40),'level':'Intermedio','cert':'Advanced Open Water','tone':'wall',
     'summary':'Caídas verticales hacia el azul, con gorgonias, esponjas y sensación de vacío.',
     'body':'En una pared se bucea a lo largo de un acantilado submarino que cae hacia la profundidad. La vida se concentra en grietas y salientes, y el azul abierto ofrece encuentros con pelágicos.',
     'need':'Buen control de flotabilidad y de la profundidad: el fondo puede estar muy lejos.',
     'tip':'Lleva el ordenador siempre a la vista; es fácil bajar sin darse cuenta.',
     'where':"(fold(p.dive_type) LIKE '%pared%' OR fold(p.dive_type) LIKE '%wall%')"},
    {'slug':'pecios y naufragios','label':'Pecios y naufragios','depth':(12,40),'level':'Intermedio','cert':'Advanced + especialidad de pecios','tone':'wreck',
     'summary':'Barcos, aviones y estructuras hundidas convertidas en arrecifes artificiales.',
     'body':'Un pecio mezcla historia y vida marina: cascos colonizados por corales, bancos de peces y rincones con mucha luz o ninguna. Recorrerlo por fuera es accesible; entrar dentro exige formación específica.',
     'need':'Certificación avanzada. Para penetrar en el pecio, especialidad y equipo adecuados.',
     'tip':'Pregunta al centro por la corriente sobre el pecio y por el plan de penetración.',
     'where':"(fold(p.dive_type) LIKE '%pecio%' OR fold(p.dive_type) LIKE '%naufrag%' OR fold(p.dive_type) LIKE '%wreck%' OR fold(p.name) LIKE '%wreck%' OR fold(p.description) LIKE '%naufrag%')"},
    {'slug':'cuevas y cavernas','label':'Cuevas y cavernas','depth':(5,30),'level':'Formación específica','cert':'Cavern / Cave','tone':'cave',
     'summary':'Túneles, arcos y cavidades donde la luz entra a rayos.',
     'body':'Las cavernas permiten bucear con la salida a la vista; las cuevas van más allá de la luz natural. Son inmersiones espectaculares por la luz y la roca, y muy exigentes en procedimientos.',
     'need':'Para cavernas, especialidad; para cuevas, formación técnica de cueva y guía.',
     'tip':'No entres nunca en una cavidad sin línea guía ni sin la formación que exige.',
     'where':"((fold(p.dive_type) LIKE '%cueva%' OR fold(p.dive_type) LIKE '%caverna%' OR fold(p.dive_type) LIKE '%tunel%') AND fold(p.name) NOT LIKE '%cenote%' AND fold(p.description) NOT LIKE '%cenote%')"},
    {'slug':'cenotes','label':'Cenotes','depth':(5,40),'level':'Formación específica','cert':'Cavern para la zona iluminada','tone':'cenote',
     'summary':'Pozos de agua dulce cristalina con haloclinas y haces de luz.',
     'body':'Los cenotes son sistemas de agua dulce y salada conectados bajo tierra. Visibilidad casi infinita, haloclinas que parecen espejos y rayos de luz que atraviesan el agua.',
     'need':'Para la zona de caverna basta con Open Water y guía; para cueva, formación técnica.',
     'tip':'Evita protector solar y repelente antes de entrar: el agua se contamina con facilidad.',
     'where':"(fold(p.dive_type) LIKE '%cenote%' OR fold(p.name) LIKE '%cenote%' OR fold(p.description) LIKE '%cenote%')"},
    {'slug':'muck','label':'Muck','depth':(3,20),'level':'Todos los niveles','cert':'Open Water','tone':'muck',
     'summary':'Fondos de arena y limo para buscar criaturas raras y macrofotografía.',
     'body':'El muck diving consiste en explorar despacio fondos aparentemente vacíos donde viven pulpos mimo, caballitos de mar, peces rana y nudibranquios. Es el paraíso de la fotografía macro.',
     'need':'Flotabilidad muy fina para no levantar sedimento.',
     'tip':'Un buen guía local multiplica lo que verás.',
     'where':"(fold(p.dive_type) LIKE '%muck%' OR fold(p.description) LIKE '%muck%' OR fold(p.description) LIKE '%lodo%')"},
    {'slug':'canales','label':'Canales','depth':(10,30),'level':'Intermedio','cert':'Advanced Open Water','tone':'channel',
     'summary':'Pasos entre arrecifes donde el agua se concentra y llegan los grandes peces.',
     'body':'Los canales conectan una laguna con el mar abierto. Con la marea entrante atraen tiburones, mantas y bancos de peces, y la inmersión suele planificarse con la corriente.',
     'need':'Experiencia con corriente y uso de boya de superficie.',
     'tip':'Pregunta al centro a qué hora entra la marea: cambia por completo la inmersión.',
     'where':"(fold(p.dive_type) LIKE '%canal%' OR fold(p.dive_type) LIKE '%channel%')"},
    {'slug':'cañones','label':'Cañones','depth':(15,40),'level':'Avanzado','cert':'Advanced Open Water','tone':'canyon',
     'summary':'Corredores encajados entre paredes de roca.',
     'body':'Un cañón submarino es un valle estrecho con paredes a ambos lados. Ofrece relieve espectacular, juegos de luz y a menudo vida pelágica en su boca.',
     'need':'Control de profundidad y de la orientación.',
     'tip':'Planifica bien el punto de giro: es fácil seguir bajando.',
     'where':"(fold(p.dive_type) LIKE '%canon%' OR fold(p.dive_type) LIKE '%canyon%')"},
    {'slug':'pináculos','label':'Pináculos','depth':(8,35),'level':'Intermedio','cert':'Advanced Open Water','tone':'pinnacle',
     'summary':'Agujas de roca que suben desde el fondo y concentran la vida a su alrededor.',
     'body':'Los pináculos y bajos son montañas submarinas aisladas. Al recibir corriente por todas partes reúnen bancos de peces, depredadores y mucho color.',
     'need':'Experiencia con corriente y descensos en azul.',
     'tip':'Baja por el cabo del barco y rodea el pináculo en espiral ascendente.',
     'where':"(fold(p.dive_type) LIKE '%pinnacle%' OR fold(p.dive_type) LIKE '%pinaculo%' OR fold(p.dive_type) LIKE '%pico%')"},
    {'slug':'corrientes y deriva','label':'Corrientes y deriva','depth':(10,30),'level':'Avanzado','cert':'Advanced + especialidad de deriva','tone':'drift',
     'summary':'Déjate llevar por la corriente y recorre kilómetros sin aletear.',
     'body':'En una deriva el barco te sigue mientras la corriente te transporta. Es una sensación parecida a volar y permite ver mucha más superficie de arrecife.',
     'need':'Boya de superficie, descensos rápidos y buena coordinación con el grupo.',
     'tip':'Mantente cerca del guía y lleva siempre señalización de superficie.',
     'where':"(fold(p.dive_type) LIKE '%corriente%' OR fold(p.dive_type) LIKE '%deriva%' OR fold(p.dive_type) LIKE '%drift%')"},
    {'slug':'aguas profundas','label':'Aguas profundas','depth':(30,40),'level':'Avanzado','cert':'Advanced Open Water / Deep','tone':'deep',
     'summary':'Puntos que alcanzan los 30 metros o más, para buceadores con experiencia.',
     'body':'Las inmersiones profundas dan acceso a paisajes y especies que no se ven cerca de la superficie. Requieren más gas, más planificación y atención a la narcosis y a la descompresión.',
     'need':'Certificación avanzada o especialidad de profundidad, según el límite del punto.',
     'tip':'Valora el nitrox para alargar el tiempo sin descompresión.',
     'where':"(p.max_depth IS NOT NULL AND CAST(p.max_depth AS REAL) >= 30)"},
    {'slug':'nocturnas','label':'Nocturnas','depth':(3,18),'level':'Intermedio','cert':'Open Water + especialidad nocturna','tone':'night',
     'summary':'El mismo arrecife, otra vida: la que sale cuando se apaga el sol.',
     'body':'De noche aparecen cazadores, crustáceos y plancton bioluminiscente. Una zona que conoces de día se convierte en otra inmersión.',
     'need':'Linterna principal y de respaldo; el centro suele exigir especialidad o experiencia.',
     'tip':'Apaga la linterna un momento para ver la bioluminiscencia.',
     'where':"(fold(p.dive_type) LIKE '%nocturn%' OR fold(p.dive_type) LIKE '%night%')"},
    {'slug':'lagos','label':'Lagos','depth':(3,30),'level':'Todos los niveles','cert':'Open Water','tone':'lake',
     'summary':'Agua dulce, paisajes sumergidos y temperatura muy distinta al mar.',
     'body':'Bucear en un lago es distinto: no hay sal, la flotabilidad cambia y aparecen bosques sumergidos, restos y fauna de agua dulce.',
     'need':'Ajustar el lastre (en agua dulce se flota menos) y protección térmica.',
     'tip':'Si el lago está en altura, la tabla de inmersión cambia: pregunta al centro.',
     'where':"(fold(p.dive_type) LIKE '%lago%' OR fold(p.dive_type) LIKE '%lake%')"},
    {'slug':'pilares','label':'Pilares','depth':(5,25),'level':'Todos los niveles','cert':'Open Water','tone':'pillar',
     'summary':'Columnas y formaciones verticales que sostienen mucha vida.',
     'body':'Pilares naturales o estructuras como muelles crean refugio para peces y fauna fija. Son inmersiones fotogénicas y fáciles de orientar.',
     'need':'Certificación básica.',
     'tip':'Mira hacia arriba: las siluetas a contraluz dan las mejores fotos.',
     'where':"(fold(p.dive_type) LIKE '%pilar%' OR fold(p.dive_type) LIKE '%pillar%')"},
    {'slug':'playa y esnórquel','label':'Playa y esnórquel','depth':(0,10),'level':'Iniciación','cert':'Sin certificación (esnórquel) / Open Water','tone':'beach',
     'summary':'Entradas desde la orilla y puntos para disfrutar con tubo y aletas.',
     'body':'Sin barco ni horarios: se entra caminando desde la playa. Perfecto para iniciarse, para bautizos y para quien prefiere el esnórquel.',
     'need':'Nada especial para esnórquel; para buceo, certificación básica.',
     'tip':'Consulta el estado del mar: el oleaje en la orilla decide si se puede entrar.',
     'where':"(fold(p.dive_type) LIKE '%snorquel%' OR fold(p.dive_type) LIKE '%snorkel%' OR fold(p.dive_type) LIKE '%playa%' OR fold(p.dive_type) LIKE '%beach%')"},
]
DIVE_CATEGORY_CENTER_HINTS = {'arrecifes': [], 'paredes': [], 'pecios y naufragios': ['pecio', 'wreck'], 'cuevas y cavernas': ['cueva', 'cave', 'caverna'], 'cenotes': ['cenote'], 'muck': ['macro', 'muck'], 'canales': [], 'cañones': [], 'pináculos': [], 'corrientes y deriva': ['deriva', 'drift'], 'aguas profundas': ['profund', 'deep', 'tecnico', 'tecrec'], 'nocturnas': ['noctur', 'night'], 'lagos': ['lago'], 'pilares': [], 'playa y esnórquel': ['esnorquel', 'snorkel', 'bautizo']}
DIVE_CATEGORY_BY_KEY = {}
for _c in DIVE_CATEGORIES:
    DIVE_CATEGORY_BY_KEY[_c['slug']] = _c
    DIVE_CATEGORY_BY_KEY[_c['label'].lower()] = _c


def dive_category(value):
    """Find a category by slug or label, ignoring case and accents."""
    if not value: return None
    v=str(value).strip().lower()
    if v in DIVE_CATEGORY_BY_KEY: return DIVE_CATEGORY_BY_KEY[v]
    fv=fold_text(v).replace('-',' ')
    for c in DIVE_CATEGORIES:
        if fold_text(c['slug'])==fv or fold_text(c['label'])==fv: return c
    return None


def dive_category_public(c):
    return {k:c[k] for k in ('slug','label','summary','body','need','tip','level','cert','tone')} | {'key':fold_text(c['slug']).replace(' ','-'),'depth_min':c['depth'][0],'depth_max':c['depth'][1]}


class Snapshot:
    """A value computed from the database and shared by every thread of a process.
    Readers always get an answer at once: when it is older than `ttl`, one background thread
    rebuilds it while everyone keeps using the previous version (no visitor waits for a rebuild)."""
    def __init__(self, name, build, ttl=60):
        self.name=name; self.build=build; self.ttl=ttl; self.value=None; self.at=0.0
        self.lock=threading.Lock(); self.refreshing=False

    def get(self, db):
        v=self.value
        if v is not None and time.time()-self.at<self.ttl: return v
        if v is None:
            with self.lock:
                if self.value is None:
                    self.value=self.build(db); self.at=time.time()
            return self.value
        with self.lock:
            if self.refreshing: return v
            self.refreshing=True
        threading.Thread(target=self._refresh, name=f'snapshot-{self.name}', daemon=True).start()
        return v

    def invalidate(self):
        """Called after an edit: this process rebuilds on its next read (others within `ttl`)."""
        self.value=None; self.at=0.0

    def _refresh(self):
        db=None
        try:
            db=connect(); value=self.build(db)
            self.value=value; self.at=time.time()
        except Exception as e:
            sys.stderr.write(f'[snapshot {self.name}] {type(e).__name__}: {e}\n')
        finally:
            self.refreshing=False
            if db is not None: db.close()




def cat_key(c):
    return fold_text(c['slug']).replace(' ','-')


def dive_types_overview(db):
    """Counts per category for the «Tipos de buceo» pages, built from the in-memory catalogue snapshots."""
    return DIVE_TYPES.get(db)


def _build_dive_types(db):
    pts=points_snapshot(db); rows=pts['rows']; items=[]
    for c in DIVE_CATEGORIES:
        key=cat_key(c); mine=[r for r in rows if key in r['types']]
        by_country={}
        for r in mine: by_country[r['country']]=by_country.get(r['country'],0)+1
        top=sorted(by_country.items(),key=lambda x:(-x[1],x[0] or ''))[:4]
        items.append(dive_category_public(c)|{'count':len(mine),'countries':len(by_country),'centers':len(category_center_ids(db,c)),
                                              'top_countries':[{'name':n,'count':k} for n,k in top]})
    return {'items':items,'totals':{'points':len(rows),'countries':len({r['country'] for r in rows}),'centers':len(directory_snapshot(db)['rows'])}}


def category_center_ids(db, cat):
    """Centers that offer a dive type: linked to one of its points, or listing it among their specialties."""
    pts=points_snapshot(db); dirs=directory_snapshot(db)
    memo=dirs.setdefault('_cats',{}); key=(id(pts),cat['slug'])
    if key in memo: return memo[key]
    k=cat_key(cat); by_id=pts['by_id']
    ids={cid for cid,pid in pts['links'] if k in (by_id.get(pid) or {}).get('types',())}
    hints=DIVE_CATEGORY_CENTER_HINTS.get(cat['slug'],[])
    if hints: ids|={r['id'] for r in dirs['rows'] if any(h in r['_spec'] for h in hints)}
    active={r['id'] for r in dirs['rows']}
    memo[key]=ids&active
    return memo[key]


def dive_type_detail(db, slug):
    c=dive_category(slug)
    if not c: return None
    overview={x['slug']:x for x in dive_types_overview(db)['items']}
    k=cat_key(c); mine=[r for r in points_snapshot(db)['rows'] if k in r['types']]
    points=sorted(mine,key=lambda r:(-r['photo_count'],r['country'] or '',r['_name']))[:60]
    snap=directory_snapshot(db); key=DIRECTORY_SORT_KEYS['recommended']
    ids=category_center_ids(db,c)
    centers=sorted([r for r in snap['rows'] if r['id'] in ids],key=key)[:8]
    centers_scope='type'
    if len(centers)<4:
        # Few centers declare this type yet: suggest centers in the countries where these dives are.
        countries={r['country'] for r in mine}
        more=sorted([r for r in snap['rows'] if r['id'] not in ids and r['country'] in countries],key=key)[:8-len(centers)]
        if more: centers_scope='mixed' if centers else 'country'; centers=centers+more
    related=[overview[x['slug']] for x in DIVE_CATEGORIES if x['slug']!=c['slug'] and x['level']==c['level'] and overview[x['slug']]['count']>0][:4]
    if len(related)<3: related+= [overview[x['slug']] for x in DIVE_CATEGORIES if x['slug']!=c['slug'] and overview[x['slug']] not in related and overview[x['slug']]['count']>0][:3-len(related)]
    return {'item':overview[c['slug']],'points':[public_point_row(p) for p in points],'centers':[public_directory_row(r) for r in centers],'centers_scope':centers_scope,'related':related}


def directory_row(r):
    d=dict(r)
    if d.get('logo_url') and is_homepage_url(d['logo_url']): d['logo_url']=None
    return d


# ---------------------------------------------------------------------------
# Center directory (public «Centros» page): one query with pre-aggregated subtables,
# server-side filters, sorting and pagination, so it stays fast with thousands of centers.
# ---------------------------------------------------------------------------
CENTER_DIRECTORY_SQL = """
WITH rv AS (SELECT center_id, ROUND(AVG(rating),1) AS rating_average, COUNT(*) AS review_count FROM center_reviews WHERE active=1 GROUP BY center_id),
     pt AS (SELECT cpl.center_id, COUNT(*) AS point_count FROM center_point_links cpl JOIN dive_points dp ON dp.id=cpl.dive_point_id AND dp.active=1 GROUP BY cpl.center_id),
     sv AS (SELECT center_id, COUNT(*) AS services_count, MIN(CASE WHEN service_type<>'alquiler_equipo' AND price>0 THEN price END) AS price_from,
                   MAX(service_type='curso') AS has_courses, MAX(service_type IN ('viaje','vida_a_bordo')) AS has_trips,
                   MAX(service_type='experiencia') AS has_try, MAX(booking_mode='payment') AS has_payment_mode FROM provider_services WHERE active=1 AND center_id IS NOT NULL GROUP BY center_id),
     sl AS (SELECT s.center_id, MIN(ss.slot_date) AS next_slot, SUM(CASE WHEN ss.slot_date<=date('now','+7 day') THEN ss.spots_available ELSE 0 END) AS spots_week
              FROM service_slots ss JOIN provider_services s ON s.id=ss.service_id AND s.active=1
             WHERE ss.status='open' AND ss.spots_available>0 AND ss.slot_date>=date('now') GROUP BY s.center_id)
SELECT c.id,c.name,c.city,c.region,c.country,c.tagline,c.description,c.specialties,c.logo_url,c.cover_url,c.website,c.verification_status,
       COALESCE(rv.rating_average,0) AS rating_average, COALESCE(rv.review_count,0) AS review_count, COALESCE(pt.point_count,0) AS point_count,
       COALESCE(sv.services_count,0) AS services_count, sv.price_from, COALESCE(sv.has_courses,0) AS has_courses, COALESCE(sv.has_trips,0) AS has_trips, COALESCE(sv.has_try,0) AS has_try,
       sl.next_slot, COALESCE(sl.spots_week,0) AS spots_week, COALESCE(sv.has_payment_mode,0) AS has_payment_mode,
       c.stripe_account_id, c.stripe_charges_enabled, c.stripe_payouts_enabled
  FROM centers c LEFT JOIN rv ON rv.center_id=c.id LEFT JOIN pt ON pt.center_id=c.id LEFT JOIN sv ON sv.center_id=c.id LEFT JOIN sl ON sl.center_id=c.id
"""




def directory_snapshot(db):
    """All active centers with their aggregates. The aggregate query reads every future departure,
    so it runs once a minute in the background; filtering and sorting thousands of rows in memory is instant."""
    return DIRECTORY.get(db)


def _build_directory(db):
    rows=[]
    for r in db.execute(CENTER_DIRECTORY_SQL+' WHERE c.active=1').fetchall():
        d=directory_row(r)
        # «Confirmación inmediata»: at least one «Pago al reservar» service that can be booked now.
        d['instant']=bool(d.pop('has_payment_mode',0)) and center_payments_ready(r)
        for k in ('stripe_account_id','stripe_charges_enabled','stripe_payouts_enabled'): d.pop(k,None)
        d['_text']=fold_text(' '.join(str(d.get(k) or '') for k in ('name','city','region','specialties','tagline')))
        d['_name']=fold_text(d.get('name')); d['_spec']=fold_text(d.get('specialties'))
        rows.append(d)
    return {'rows':rows}


def directory_category_ids(db, cat):
    return category_center_ids(db, cat)


DIRECTORY_SORT_KEYS={
    'recommended':lambda r:(-(r['services_count']>0),-(r['next_slot'] is not None),-r['review_count'],-(bool(r.get('cover_url'))),r['_name']),
    'rating':lambda r:(r['review_count']==0,-r['rating_average'],-r['review_count'],r['_name']),
    'reviews':lambda r:(-r['review_count'],-r['rating_average'],r['_name']),
    'price':lambda r:(r['price_from'] is None,r['price_from'] or 0,r['_name']),
    'name':lambda r:r['_name'],
}
DIRECTORY_FLAGS={'instant':lambda r:bool(r.get('instant')),'online':lambda r:r['services_count']>0,'week':lambda r:r['spots_week']>0,'courses':lambda r:r['has_courses']==1,
                 'trips':lambda r:r['has_trips']==1,'try':lambda r:r['has_try']==1,'reviews':lambda r:r['review_count']>0}


def with_booking_flags(db, d):
    """Adds the «Confirmación inmediata» flag and the number of bookable services from the directory snapshot."""
    row = next((x for x in directory_snapshot(db)['rows'] if x['id'] == d.get('id')), None)
    d['instant'] = bool(row and row.get('instant')); d['services_count'] = int(row['services_count']) if row else 0
    return d


def public_directory_row(r):
    return {k:v for k,v in r.items() if not k.startswith('_')}


def center_directory(db, query):
    g=lambda k,d='': (query.get(k,[d])[0] or d)
    rows=directory_snapshot(db)['rows']
    q=fold_text(clean_text(g('q'),120) or '').strip()
    if q:
        words=q.split()
        rows=[r for r in rows if all(w in r['_text'] for w in words)]
    for f in [x for x in g('only').split(',') if x in DIRECTORY_FLAGS]:
        rows=[r for r in rows if DIRECTORY_FLAGS[f](r)]
    point=g('point')
    if point.isdigit():
        ids={x[0] for x in db.execute('SELECT center_id FROM center_point_links WHERE dive_point_id=?',(int(point),))}
        rows=[r for r in rows if r['id'] in ids]
    cat=dive_category(g('type'))
    if cat:
        ids=directory_category_ids(db,cat); rows=[r for r in rows if r['id'] in ids]
    # Country facet ignores the country filter itself so people can switch country.
    facet={}
    for r in rows: facet[r['country']]=facet.get(r['country'],0)+1
    country=clean_text(g('country'),120)
    if country: rows=[r for r in rows if r['country']==country]
    rows=sorted(rows,key=DIRECTORY_SORT_KEYS.get(g('sort','recommended'),DIRECTORY_SORT_KEYS['recommended']))
    try: per=max(1,min(60,int(g('per_page','24')))); page=max(1,min(10000,int(g('page','1'))))
    except ValueError: per,page=24,1
    total=len(rows)
    items=[public_directory_row(r) for r in rows[(page-1)*per:page*per]]
    countries=sorted(facet.items(),key=lambda x:(-x[1],x[0] or ''))
    return {'items':items,'total':total,'page':page,'per_page':per,'pages':(total+per-1)//per,'countries':[{'name':n,'count':k} for n,k in countries]}


def is_homepage_url(url):
    """A bare website address (no path) stored where an image was expected."""
    u=str(url or '').strip()
    if not u or u.startswith('/'): return False
    rest=re.sub(r'^https?://','',u,flags=re.I).split('?')[0].split('#')[0]
    return '/' not in rest.rstrip('/')


SPECIALTY_ES = {'scuba diving':'Buceo recreativo','snorkelling':'Esnórquel','snorkeling':'Esnórquel','courses':'Cursos','conservation':'Conservación',
    'tecrec':'Buceo técnico','technical':'Buceo técnico','nitrox':'Nitrox','freediving':'Apnea','wreck':'Pecios','professional':'Formación profesional',
    'travel':'Viajes de buceo','caves':'Cuevas','adaptive':'Buceo adaptado','equipment':'Tienda y material','dpv':'Scooter (DPV)','deep':'Buceo profundo',
    'rescue':'Rescate','nature reserves':'Reservas marinas','night':'Nocturnas'}


def migrate_center_directory_data(db):
    """One-off clean-up of imported centers (idempotent): Spanish country name, Spanish specialties,
    and websites that were stored in logo_url (they are not images)."""
    db.execute("UPDATE centers SET country='España' WHERE country IN ('Spain','spain','ESPAÑA','Espana')")
    for r in db.execute("SELECT id,specialties FROM centers WHERE specialties LIKE '%;%'").fetchall():
        parts=[p.strip() for p in r['specialties'].split(';') if p.strip()]
        out=[]
        for p in parts:
            t=SPECIALTY_ES.get(p.lower(),p)
            if t not in out: out.append(t)
        db.execute('UPDATE centers SET specialties=? WHERE id=?',(' · '.join(out),r['id']))
    for r in db.execute("SELECT id,logo_url,website FROM centers WHERE logo_url IS NOT NULL AND logo_url<>''").fetchall():
        if not is_homepage_url(r['logo_url']): continue
        if not (r['website'] or '').strip(): db.execute('UPDATE centers SET website=?,logo_url=NULL WHERE id=?',(r['logo_url'],r['id']))
        else: db.execute('UPDATE centers SET logo_url=NULL WHERE id=?',(r['id'],))




# ---------------------------------------------------------------------------
# Public catalogue of dive points: one in-memory snapshot per process, refreshed every minute.
# It feeds the points directory, the map layer, the home search and the Top 10, so none of
# those pages scan or aggregate the database on every visit.
# ---------------------------------------------------------------------------
POINT_LEVELS={'start':('principiante','iniciacion','facil'),'mid':('intermedio','intermedia','moderado'),'adv':('avanzado',)}


def point_level(difficulty):
    d=fold_text(difficulty)
    for k,words in POINT_LEVELS.items():
        if any(w in d for w in words): return k
    return ''


def points_snapshot(db):
    return POINTS.get(db)


def _build_points(db):
    rows=db.execute("""
        WITH cr AS (SELECT center_id, ROUND(AVG(rating),1) AS avg_r, COUNT(*) AS n FROM center_reviews WHERE active=1 GROUP BY center_id),
             links AS (SELECT dive_point_id, center_id FROM center_point_links UNION SELECT id, center_id FROM dive_points WHERE center_id IS NOT NULL),
             pc AS (SELECT l.dive_point_id, COUNT(DISTINCT l.center_id) AS centers,
                           MAX(COALESCE(cr.avg_r,0)) AS rating_average, MAX(COALESCE(cr.n,0)) AS review_count
                      FROM links l JOIN centers ce ON ce.id=l.center_id AND ce.active=1 LEFT JOIN cr ON cr.center_id=l.center_id GROUP BY l.dive_point_id),
             ph AS (SELECT dive_point_id, COUNT(*) AS n FROM dive_point_photos WHERE image_path NOT IN ('/assets/images/fondo1.webp','/assets/images/buceador1.png','/assets/images/buceador2.png') GROUP BY dive_point_id)
        SELECT p.id,p.name,p.country,p.region,p.zone,p.subregion,p.dive_type,p.difficulty,p.min_depth,p.max_depth,p.latitude,p.longitude,
               p.verification_status,p.description,
               COALESCE(pc.centers,0) AS centers_count, COALESCE(pc.rating_average,0) AS rating_average, COALESCE(pc.review_count,0) AS review_count,
               COALESCE(ph.n,0) AS photo_count,
               (SELECT image_path FROM dive_point_photos x WHERE x.dive_point_id=p.id AND x.image_path NOT IN ('/assets/images/fondo1.webp','/assets/images/buceador1.png','/assets/images/buceador2.png') ORDER BY sort_order,id LIMIT 1) AS photo
          FROM dive_points p LEFT JOIN pc ON pc.dive_point_id=p.id LEFT JOIN ph ON ph.dive_point_id=p.id
         WHERE p.active=1""").fetchall()
    type_ids={}
    for cat in DIVE_CATEGORIES:
        for (pid,) in db.execute(f"SELECT p.id FROM dive_points p WHERE p.active=1 AND {cat['where']}"):
            type_ids.setdefault(pid,[]).append(fold_text(cat['slug']).replace(' ','-'))
    out=[]; by_id={}
    for r in rows:
        d=dict(r)
        for k in ('min_depth','max_depth','latitude','longitude'):
            try: d[k]=float(d[k]) if d[k] not in (None,'') else None
            except (TypeError,ValueError): d[k]=None
        desc=d.pop('description') or ''
        # Generic catalogue sentences say nothing to a visitor: no excerpt rather than boilerplate.
        boiler=re.search(r'cat[aá]logo inicial|pendiente de (verificaci|ampliar|completar)|ubicaci[oó]n de referencia',desc,re.I)
        d['excerpt']='' if boiler else ((desc[:157]+'…') if len(desc)>160 else desc)
        d['types']=type_ids.get(d['id'],[])
        d['level']=point_level(d.get('difficulty'))
        d['_text']=fold_text(' '.join(str(x or '') for x in (d['name'],d['country'],d['region'],d['zone'],d['subregion'],d['dive_type'],desc)))
        d['_name']=fold_text(d['name'])
        out.append(d); by_id[d['id']]=d
    zones={}
    for d in out:
        z=zones.setdefault(d['zone'] or 'Otros',{'name':d['zone'] or 'Otros','count':0,'subregions':{}})
        z['count']+=1; s=d['subregion'] or d['region'] or d['country']
        z['subregions'][s]=z['subregions'].get(s,0)+1
    facets={'zones':[{'name':z['name'],'count':z['count'],'subregions':[{'name':k,'count':v} for k,v in sorted(z['subregions'].items(),key=lambda x:(-x[1],x[0]))]} for z in sorted(zones.values(),key=lambda z:-z['count'])]}
    links=[(r[0],r[1]) for r in db.execute('''SELECT l.center_id, l.dive_point_id FROM (SELECT center_id, dive_point_id FROM center_point_links
                                                   UNION SELECT center_id, id FROM dive_points WHERE center_id IS NOT NULL AND active=1) l
                                               JOIN centers c ON c.id=l.center_id AND c.active=1''')]
    return {'rows':out,'by_id':by_id,'facets':facets,'links':links}


def public_point_row(d):
    return {k:v for k,v in d.items() if not k.startswith('_')}


POINT_SORTS={
    'recommended':lambda r:(-(r['photo_count']>0),-r['centers_count'],-r['review_count'],r['_name']),
    'name':lambda r:r['_name'],
    'rating':lambda r:(r['review_count']==0,-r['rating_average'],-r['review_count'],r['_name']),
    'depth':lambda r:(r['max_depth'] is None,-(r['max_depth'] or 0),r['_name']),
    'shallow':lambda r:(r['max_depth'] is None,(r['max_depth'] or 0),r['_name']),
}


def point_directory(db, query):
    g=lambda k,d='': (query.get(k,[d])[0] or d)
    snap=points_snapshot(db)
    # Rows are pre-sorted once per snapshot and sort key; filters below keep that order (no sort per request).
    sort=g('sort','recommended'); sort=sort if sort in POINT_SORTS else 'recommended'
    cache=snap.setdefault('_sorted',{})
    if sort not in cache: cache[sort]=sorted(snap['rows'],key=POINT_SORTS[sort])
    rows=cache[sort]
    q=fold_text(clean_text(g('q'),120) or '').strip()
    if q:
        words=q.split(); rows=[r for r in rows if all(w in r['_text'] for w in words)]
    cat=dive_category(g('type'))
    if cat:
        key=fold_text(cat['slug']).replace(' ','-'); rows=[r for r in rows if key in r['types']]
    level=g('level')
    if level in POINT_LEVELS: rows=[r for r in rows if r['level']==level]
    if g('only')=='centers': rows=[r for r in rows if r['centers_count']>0]
    if g('only')=='instant' or g('instant')=='1':
        # «Confirmación inmediata»: dive sites where at least one centre offers «Pago al reservar» bookable now.
        inst={x['id'] for x in directory_snapshot(db)['rows'] if x.get('instant')}
        ids={x[0] for x in db.execute('SELECT DISTINCT dive_point_id FROM center_point_links WHERE center_id IN (%s)'%(','.join('?'*len(inst)) or 'NULL'),list(inst)).fetchall()} if inst else set()
        rows=[r for r in rows if r['id'] in ids]
    # Facets are computed before the geographic filters so the visitor can always switch zone or country.
    zone=clean_text(g('zone'),120); sub=clean_text(g('subregion'),120); country=clean_text(g('country'),120)
    zf={}; cf={}
    for r in rows:
        zf[r['zone'] or 'Otros']=zf.get(r['zone'] or 'Otros',0)+1
    if zone: rows=[r for r in rows if (r['zone'] or 'Otros')==zone]
    for r in rows: cf[r['country']]=cf.get(r['country'],0)+1
    if country: rows=[r for r in rows if r['country']==country]
    if sub: rows=[r for r in rows if (r['subregion'] or r['region'] or r['country'])==sub]
    try: per=max(1,min(60,int(g('per_page','24')))); page=max(1,min(10000,int(g('page','1'))))
    except ValueError: per,page=24,1
    total=len(rows)
    return {'items':[public_point_row(r) for r in rows[(page-1)*per:page*per]],'total':total,'page':page,'per_page':per,'pages':(total+per-1)//per,
            'zones':[{'name':k,'count':v} for k,v in sorted(zf.items(),key=lambda x:-x[1])],
            'countries':[{'name':k,'count':v} for k,v in sorted(cf.items(),key=lambda x:(-x[1],x[0] or ''))]}


MAP_FIELDS=('id','name','country','region','zone','subregion','dive_type','difficulty','latitude','longitude','min_depth','max_depth','types')


def points_map_payload(db):
    """Everything the map, the zone list and the instant search need. Rows travel as arrays (field names once),
    and the JSON and its gzip version are built once per snapshot: serving the map costs no CPU per visitor."""
    snap=points_snapshot(db)
    cached=snap.get('_map')
    if cached: return cached
    rows=[[r[f] for f in MAP_FIELDS] for r in snap['rows'] if r['latitude'] is not None and r['longitude'] is not None]
    raw=json.dumps({'fields':MAP_FIELDS,'rows':rows,'zones':snap['facets']['zones'],'total':len(snap['rows'])},ensure_ascii=False,separators=(',',':')).encode('utf-8')
    cached=(raw,gzip_bytes(raw,6)); snap['_map']=cached
    return cached


def haversine_km(lat1, lon1, lat2, lon2):
    p1,p2=math.radians(lat1),math.radians(lat2); dp=math.radians(lat2-lat1); dl=math.radians(lon2-lon1)
    a=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 6371.0088*2*math.atan2(math.sqrt(a),math.sqrt(max(0,1-a)))


def nearby_points(db, lat, lon, radius_km, exclude=None, limit=6):
    snap=points_snapshot(db); dlat=radius_km/111.0; out=[]
    for r in snap['rows']:
        if r['id']==exclude or r['latitude'] is None or r['longitude'] is None: continue
        if abs(r['latitude']-lat)>dlat: continue  # cheap box filter before the exact distance
        km=haversine_km(lat,lon,r['latitude'],r['longitude'])
        if km<=radius_km: out.append((km,r))
    out.sort(key=lambda x:x[0])
    return [dict(public_point_row(r),distance_km=round(km,1)) for km,r in out[:limit]]


def top_dives(db, lat, lon, radius_km):
    snap=points_snapshot(db); dlat=radius_km/111.0; ranked=[]
    for r in snap['rows']:
        if r['latitude'] is None or r['longitude'] is None or abs(r['latitude']-lat)>dlat: continue
        km=haversine_km(lat,lon,r['latitude'],r['longitude'])
        if km>radius_km: continue
        rating=float(r['rating_average'] or 0); reviews=int(r['review_count'] or 0)
        # Until point-level reviews exist, centre reviews are the strongest available social signal.
        # Proximity is deliberately secondary so the list stays a "best dives" list, not a nearest-points list.
        social=(rating/5.0)*0.78+min(reviews,20)/20.0*0.22 if reviews else 0.45
        score=social*0.82+max(0.0,1.0-(km/radius_km))*0.18
        ranked.append(dict(public_point_row(r),distance_km=round(km,1),top_score=round(score,4)))
    ranked.sort(key=lambda x:(-x['top_score'],x['distance_km'],x['name'].lower()))
    out={'items':ranked[:10],'radius_km':radius_km,'has_reviews':any(x['review_count'] for x in ranked),'candidates':len(ranked),'nearest':None}
    if not ranked:
        # Nothing inside the radius: tell the visitor where the closest dive site is, so the page never looks broken.
        best=None
        for r in snap['rows']:
            if r['latitude'] is None or r['longitude'] is None: continue
            km=haversine_km(lat,lon,r['latitude'],r['longitude'])
            if best is None or km<best[0]: best=(km,r)
        if best: out['nearest']=dict(public_point_row(best[1]),distance_km=round(best[0],1))
    return out


# ---------------------------------------------------------------------------
# Experiences directory: destinations with what is published in each (cached one minute).
# ---------------------------------------------------------------------------
def travel_directory(db):
    return TRAVEL.get(db)


def _build_travel(db):
    offers=db.execute('SELECT * FROM travel_offers WHERE active=1 ORDER BY title').fetchall()
    exps=db.execute('''SELECT e.*, u.fullname AS provider_name, c.name AS center_name FROM travel_experiences e
                         LEFT JOIN users u ON u.id=e.provider_user_id LEFT JOIN centers c ON c.id=e.center_id
                        WHERE e.active=1 AND e.status='published'
                          AND (e.service_id IS NULL OR EXISTS(SELECT 1 FROM provider_services ps WHERE ps.id=e.service_id AND ps.active=1))''').fetchall()
    by_offer={}
    for e in enrich_experiences(db,exps): by_offer.setdefault(e['travel_offer_id'],[]).append(e)
    today=datetime.now().date().isoformat(); items=[]
    for o in offers:
        lst=by_offer.get(o['id'],[])
        prices=[float(e['price']) for e in lst if e.get('price') not in (None,'') and float(e['price'])>0]
        dates=sorted(d for d in ([e.get('start_date') for e in lst]+[x['slot_date'] for e in lst for x in (e.get('departures') or [])]) if d and d>=today)
        providers={(e.get('center_id') or 0, e.get('provider_user_id') or 0) for e in lst}
        items.append(dict(o)|{'experiences':len(lst),'providers':len(providers),'price_from':min(prices) if prices else None,
                              'currency':(lst[0].get('currency') if lst else None) or 'EUR','next_date':dates[0] if dates else None})
    items.sort(key=lambda x:(-x['experiences'],x['title']))
    return {'items':items,'kinds':sorted({i['kind'] for i in items if i.get('kind')})}


_GZIP_CACHE={}


def gzip_bytes(raw, level=5):
    import gzip as _gz
    return _gz.compress(raw, compresslevel=level, mtime=0)




# ---------------------------------------------------------------------------
# Editable images of the public site (section covers and dive-type photos).
# Defaults live here; an administrator replaces any of them from «Imágenes de la web».
# ---------------------------------------------------------------------------
SITE_MEDIA_SLOTS = [
    # key, label, where it appears, default image, recommended size
    ('hero:home', 'Portada de la web', 'Cabecera de la página de inicio', '/assets/images/portada-arrecife.webp', '2400 × 1350'),
    ('hero:centros', 'Centros de buceo', 'Cabecera del directorio de centros', '/assets/images/BUCEADORES.webp', '2400 × 900'),
    ('hero:puntos', 'Puntos de buceo', 'Cabecera del catálogo de puntos', '/assets/images/australia.webp', '2400 × 900'),
    ('hero:tipos', 'Tipos de buceo', 'Cabecera de la página de tipos', '/assets/images/fondo.webp', '2400 × 900'),
    ('hero:experiencias', 'Experiencias', 'Cabecera de viajes y vida a bordo', '/assets/images/maldivas.webp', '2400 × 900'),
    ('hero:top10', 'Top 10', 'Cabecera del Top 10', '/assets/images/tailandia.webp', '2400 × 900'),
    ('hero:explorar', 'Explorar el mapa', 'Cabecera del mapa de Explorar', '/assets/images/micronesia.webp', '2400 × 900'),
    ('hero:auth', 'Iniciar sesión y registro', 'Foto junto al formulario de acceso', '/assets/images/logbook1.webp', '1600 × 2000 (vertical)'),
]
SITE_MEDIA_TYPE_DEFAULTS = {'arrecifes':'fondosuperior','paredes':'australia','pecios-y-naufragios':'logbook1','cuevas-y-cavernas':'galapagos',
    'cenotes':'mexico','muck':'tailandia','canales':'egipto','canones':'fondo','pinaculos':'BUCEADORES','corrientes-y-deriva':'fondo1',
    'aguas-profundas':'california','nocturnas':'micronesia','lagos':'fondo','pilares':'BUCEADORES','playa-y-esnorquel':'maldivas'}


def site_media_slots():
    slots=[{'key':k,'label':l,'where':w,'default':d,'size':sz,'group':'Portadas de sección'} for k,l,w,d,sz in SITE_MEDIA_SLOTS]
    for c in DIVE_CATEGORIES:
        key=cat_key(c)
        slots.append({'key':'type:'+key,'label':c['label'],'where':'Tarjeta y cabecera del tipo de buceo','default':f"/assets/images/{SITE_MEDIA_TYPE_DEFAULTS.get(key,'fondo')}.webp",'size':'1600 × 1000','group':'Tipos de buceo'})
    return slots


SITE_MEDIA_KEYS = None


def site_media_key_ok(key):
    global SITE_MEDIA_KEYS
    if SITE_MEDIA_KEYS is None: SITE_MEDIA_KEYS={s['key'] for s in site_media_slots()}
    return key in SITE_MEDIA_KEYS


def _build_site_media(db):
    custom={r['key']:dict(r) for r in db.execute('SELECT key,image_url,credit,updated_at FROM site_media').fetchall()}
    items={}
    for s in site_media_slots():
        c=custom.get(s['key']) or {}
        items[s['key']]={'url':c.get('image_url') or s['default'],'credit':c.get('credit') or '','custom':bool(c.get('image_url')),'default':s['default']}
    themes=[dict(r) for r in db.execute('SELECT id,name,accent,ribbon,mode,scope,starts_on,ends_on,updated_at FROM site_themes ORDER BY id').fetchall()]
    tm={}
    for r in db.execute('SELECT theme_id,key,image_url,credit FROM site_theme_media').fetchall():
        tm.setdefault(r['theme_id'],{})[r['key']]={'url':r['image_url'],'credit':r['credit'] or ''}
    for t in themes: t['media']=tm.get(t['id'],{})
    return {'items':items,'themes':themes}


# ---------------------------------------------------------------------------
# Seasonal looks (v50.29). The administrator prepares «temas» (summer, Christmas, whale season...)
# with their own photos and colour; each one is shown on its dates every year, for the whole world
# or only for visitors of one hemisphere (seasons are reversed in the south), or switched on by hand.
# ---------------------------------------------------------------------------
THEME_ACCENTS = ('oceano','coral','tropical','atardecer','invierno','abisal')
THEME_MODES = ('schedule','always','off')
THEME_SCOPES = ('all','north','south')


def _md(value):
    m=re.fullmatch(r'(\d{2})-(\d{2})', str(value or '').strip())
    if not m: return None
    mo,d=int(m.group(1)),int(m.group(2))
    if not (1<=mo<=12 and 1<=d<=31): return None
    return f'{mo:02d}-{d:02d}'


def _theme_span(t):
    """Days covered by a yearly range (wraps over New Year); used so a short campaign beats a whole season."""
    a,b=_md(t.get('starts_on')),_md(t.get('ends_on'))
    if not a or not b: return 999
    da=int(a[:2])*31+int(a[3:]); db_=int(b[:2])*31+int(b[3:])
    return (db_-da) if db_>=da else (12*31-da+db_)


def theme_is_on(t, md, hemi):
    if t.get('mode')=='off': return False
    if t.get('scope') not in ('all', None, '') and t.get('scope')!=hemi: return False
    if t.get('mode')=='always': return True
    a,b=_md(t.get('starts_on')),_md(t.get('ends_on'))
    if not a or not b: return False
    return (a<=md<=b) if a<=b else (md>=a or md<=b)


# ---------------------------------------------------------------------------
# Promotional QR codes (v50.29). A centre creates a promotion («Curso Open Water + 1 año de
# equipo gratis»), gives a personal code to clients it already has, and any centre of the
# promotion (the issuer and the partners that accepted) scans it to check and redeem it.
# ---------------------------------------------------------------------------
PROMO_ALPHABET='ABCDEFGHJKLMNPQRSTUVWXYZ23456789'


def new_promo_code(db):
    import secrets as _s
    for _ in range(20):
        c=''.join(_s.choice(PROMO_ALPHABET) for _ in range(10))
        if not db.execute('SELECT 1 FROM promotion_codes WHERE code=?',(c,)).fetchone(): return c
    raise RuntimeError('No se ha podido generar un código único.')


def public_base(handler):
    return handler.base_url()


_GEOCODE_CACHE = {}
_GEOCODE_LOCK = threading.Lock()
_GEOCODE_LAST = [0.0]


def geocode_search(q, lang='es'):
    """Place search through Nominatim (OpenStreetMap), cached for a day and throttled to 1 request per second for
    the whole server, with an identified User-Agent, as its usage policy requires. WOD_GEOCODER_URL can point to
    another Nominatim-compatible service (or a self-hosted one) for heavy production use."""
    key = (fold_text(q).strip(), lang)
    hit = _GEOCODE_CACHE.get(key)
    if hit and time.time() - hit[0] < 86400: return hit[1]
    import urllib.request
    base = wcfg.env('WOD_GEOCODER_URL', 'https://nominatim.openstreetmap.org/search')
    url = f"{base}?format=jsonv2&limit=6&addressdetails=0&accept-language={quote(lang)}&q={quote(q)}"
    with _GEOCODE_LOCK:
        wait = 1.05 - (time.time() - _GEOCODE_LAST[0])
        if wait > 0: time.sleep(wait)
        _GEOCODE_LAST[0] = time.time()
    try:
        req = urllib.request.Request(url, headers={'User-Agent': f'WORLDIVES-DISCOVERY/{APP_VERSION} ({public_site_url()})', 'Accept': 'application/json'})
        with urllib.request.urlopen(req, timeout=8) as resp:
            raw = json.loads(resp.read(512 * 1024).decode('utf-8'))
        items = [{'name': clean_text(x.get('display_name'), 200), 'lat': float(x['lat']), 'lon': float(x['lon'])} for x in raw if x.get('lat') and x.get('lon')][:6]
    except Exception as exc:
        sys.stderr.write(f'[geocode] {type(exc).__name__}: {exc}\n')
        return []
    if len(_GEOCODE_CACHE) > 5000: _GEOCODE_CACHE.clear()
    _GEOCODE_CACHE[key] = (time.time(), items)
    return items


def promo_state(promo_status, code_status, uses, max_uses, valid_from, valid_until, today=None):
    today=today or _dt.date.today().isoformat()
    if code_status=='revoked': return 'revoked'
    if promo_status!='active': return 'ended'
    if valid_until and valid_until<today: return 'expired'
    if valid_from and valid_from>today: return 'upcoming'
    if int(uses or 0)>=int(max_uses or 1): return 'used'
    return 'active'


PROMO_STATE_TEXT={'active':'Activa','used':'Ya utilizada','expired':'Caducada','revoked':'Anulada por el centro','ended':'Promoción finalizada','upcoming':'Todavía no ha empezado'}


def promo_centers(db, promo_id, issuer_id):
    rows=db.execute('''SELECT c.id,c.name,c.city,c.country FROM centers c WHERE c.id=? UNION ALL
                       SELECT c.id,c.name,c.city,c.country FROM promotion_partners pp JOIN centers c ON c.id=pp.center_id WHERE pp.promotion_id=? AND pp.status='accepted' ''',(issuer_id,promo_id)).fetchall()
    return [dict(r) for r in rows]


def promo_code_payload(db, row, viewer=None):
    """What a scan of a promotional QR shows. Personal data only to the holder and to centres of the promotion."""
    centers=promo_centers(db,row['promotion_id'],row['center_id'])
    st=promo_state(row['promo_status'],row['status'],row['uses'],row['uses_per_code'],row['valid_from'],row['valid_until'])
    out={'code':row['code'],'title':row['title'],'description':row['description'] or '','value_text':row['value_text'] or '','conditions':row['conditions'] or '',
         'valid_from':row['valid_from'],'valid_until':row['valid_until'],'uses':row['uses'],'max_uses':row['uses_per_code'],'state':st,'state_text':PROMO_STATE_TEXT.get(st,st),
         'issuer':{'id':row['center_id'],'name':row['center_name'],'city':row['center_city']},'centers':centers,'viewer':'public'}
    name=row['holder_name'] or ''
    out['holder']=' '.join(w[:1]+'.' for w in name.split()[:2]) if name else ''
    if viewer:
        if viewer['id']==row['user_id']: out['viewer']='holder'; out['holder']=name
        elif viewer['role'] in ('center','admin'):
            ok=viewer['role']=='admin' or any(c['id']==viewer['center_id'] for c in centers)
            out['viewer']='center_ok' if ok else 'center_other'
            if ok:
                out['holder']=name; out['holder_email']=row['holder_email']
                out['can_redeem']=st=='active' and viewer['role']=='center'
                out['redemptions']=[dict(r) for r in db.execute('''SELECT pr.created_at,c.name AS center_name,pr.note FROM promotion_redemptions pr JOIN centers c ON c.id=pr.center_id WHERE pr.code_id=? ORDER BY pr.id DESC''',(row['id'],)).fetchall()]
    return out


PROMO_CODE_SQL='''SELECT pc.*,p.title,p.description,p.value_text,p.conditions,p.valid_from,p.valid_until,p.uses_per_code,p.status AS promo_status,p.center_id,
                         c.name AS center_name,c.city AS center_city,u.fullname AS holder_name,u.email AS holder_email
                    FROM promotion_codes pc JOIN promotions p ON p.id=pc.promotion_id JOIN centers c ON c.id=p.center_id JOIN users u ON u.id=pc.user_id WHERE pc.code=?'''


def center_promotions(db, cid):
    items=[]
    for p in db.execute('SELECT * FROM promotions WHERE center_id=? ORDER BY status=\'active\' DESC, id DESC',(cid,)).fetchall():
        d=dict(p)
        d['partners']=[dict(r) for r in db.execute('SELECT pp.center_id,pp.status,c.name,c.city FROM promotion_partners pp JOIN centers c ON c.id=pp.center_id WHERE pp.promotion_id=? ORDER BY c.name',(p['id'],)).fetchall()]
        k=db.execute("SELECT COUNT(*) n,SUM(CASE WHEN status='active' THEN 1 ELSE 0 END) live,SUM(uses) used FROM promotion_codes WHERE promotion_id=?",(p['id'],)).fetchone()
        d['codes_count']=k['n'] or 0; d['codes_live']=k['live'] or 0; d['redemptions']=k['used'] or 0
        d['expired']=bool(p['valid_until'] and p['valid_until']<_dt.date.today().isoformat())
        items.append(d)
    invites=[dict(r) for r in db.execute('''SELECT p.id,p.title,p.value_text,p.valid_until,p.status AS promo_status,pp.status,c.name AS issuer_name,c.city AS issuer_city
                                              FROM promotion_partners pp JOIN promotions p ON p.id=pp.promotion_id JOIN centers c ON c.id=p.center_id
                                             WHERE pp.center_id=? ORDER BY pp.status='invited' DESC, p.id DESC''',(cid,)).fetchall()]
    return {'items':items,'network':invites}


def clean_logbook(data):
    """Validated Log Book fields: a real date, a site name and plausible depth/time."""
    d=clean_text(data.get('dive_date'),10) or ''
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',d): raise ValueError('Indica la fecha de la inmersión.')
    if d>_dt.date.today().isoformat(): raise ValueError('La fecha de la inmersión no puede ser futura.')
    site=clean_text(data.get('site'),200)
    if not site: raise ValueError('Indica el punto de buceo.')
    def num(k,lo,hi,label):
        v=data.get(k)
        if v in (None,''): return None
        try: f=float(str(v).replace(',','.'))
        except ValueError: raise ValueError(f'{label}: escribe un número.')
        if not lo<=f<=hi: raise ValueError(f'{label}: debe estar entre {lo} y {hi}.')
        return round(f,1)
    return {'dive_date':d,'site':site,'country':clean_text(data.get('country'),100) or '','depth':num('depth',0,350,'Profundidad'),
            'duration':num('duration',0,600,'Duración'),'dive_type':clean_text(data.get('dive_type'),100) or '','notes':clean_text(data.get('notes'),2000) or ''}


def is_center_client(db, cid, uid):
    return bool(db.execute('SELECT 1 FROM bookings WHERE center_id=? AND user_id=? UNION SELECT 1 FROM center_links WHERE center_id=? AND user_id=? LIMIT 1',(cid,uid,cid,uid)).fetchone())


def resolve_site_media(snap, hemi='north', preview=None, today=None):
    """Pick the look for this visitor: forced theme > dated theme (shortest range first) > custom photo > original."""
    hemi='south' if hemi in ('s','south') else 'north'
    md=(today or _dt.date.today()).strftime('%m-%d')
    themes=snap.get('themes') or []
    theme=None
    if preview:
        theme=next((t for t in themes if str(t['id'])==str(preview)),None)
    if theme is None:
        on=[t for t in themes if theme_is_on(t,md,hemi)]
        on.sort(key=lambda t:(0 if t['mode']=='always' else 1, _theme_span(t), -t['id']))
        theme=on[0] if on else None
    items=snap['items']
    if theme and theme.get('media'):
        items=dict(items)
        for k,v in theme['media'].items():
            if k in items: items[k]={**items[k],'url':v['url'],'credit':v['credit'] or items[k]['credit'],'theme':True}
    out={'items':items,'theme':None}
    if theme: out['theme']={'id':theme['id'],'name':theme['name'],'accent':theme['accent'],'ribbon':theme.get('ribbon') or '','preview':bool(preview)}
    return out


def point_photo_allowed(db, user, pid):
    """Admins manage every point; a center manages the points it operates (own or linked)."""
    if user['role']=='admin': return True
    if user['role']!='center' or not user['center_id']: return False
    return bool(db.execute('''SELECT 1 FROM dive_points p WHERE p.id=? AND (p.center_id=? OR EXISTS(SELECT 1 FROM center_point_links l WHERE l.dive_point_id=p.id AND l.center_id=?))''',(pid,user['center_id'],user['center_id'])).fetchone())


SNAPSHOT_WRITE_PREFIXES=(('/api/dive-points','POINTS','DIVE_TYPES'),('/api/center-points','POINTS','DIRECTORY','DIVE_TYPES'),('/api/admin/dive-points','POINTS','DIVE_TYPES'),
    ('/api/travel-experiences','TRAVEL'),('/api/admin/travel','TRAVEL'),('/api/centers','DIRECTORY'),('/api/provider/center','DIRECTORY'),('/api/admin/site-promos','PROMOS'),('/api/provider/center','PROMOS'),('/api/admin/centers','PROMOS'),('/api/provider/avatar','PROMOS'))


# ---------------------------------------------------------------------------
import datetime as _dt
# Planning of a center (v50.26): any month, past or future, with day detail and month figures.
# ---------------------------------------------------------------------------
def _month_bounds(month):
    m=re.fullmatch(r'(\d{4})-(\d{2})', str(month or ''))
    today=_dt.date.today()
    y,mo=(int(m.group(1)),int(m.group(2))) if m else (today.year,today.month)
    if not (2000<=y<=2100 and 1<=mo<=12): y,mo=today.year,today.month
    first=_dt.date(y,mo,1)
    nxt=_dt.date(y+(mo==12),1 if mo==12 else mo+1,1)
    return first, nxt-_dt.timedelta(days=1)


def _shift_month(d, n):
    k=d.year*12+d.month-1+n
    return _dt.date(k//12,k%12+1,1)


# A «Pago al reservar» booking whose payment was abandoned never existed for the centre: it is hidden everywhere.
CENTER_VISIBLE_SQL = "NOT (b.status='expired' AND COALESCE(b.expired_reason,'') IN ('hold_expired','payment_cancelled','checkout_failed','legacy_unpaid'))"


def planning_scope(user):
    """SQL fragments restricting services and bookings to what the signed-in center or professional owns.
    A centre sees ALL the services of the centre, whoever created them (team members included)."""
    if user['role']=='center' and user['center_id']:
        return 's.center_id=?',(int(user['center_id']),),'b.center_id=?',(int(user['center_id']),)
    if user['role']=='freelance':
        return 's.provider_user_id=?',(user['id'],),'b.service_id IN (SELECT id FROM provider_services WHERE provider_user_id=?)',(user['id'],)
    raise PermissionError('Solo los centros y profesionales tienen planning.')


def _planning_figures(db, svc_where, svc_args, bk_where, bk_args, start, end):
    slots=db.execute(f'''SELECT COUNT(*) n, COALESCE(SUM(ss.spots_total),0) offered,
                             COALESCE(SUM(MAX(ss.spots_total-ss.spots_available,0)),0) taken
                        FROM service_slots ss JOIN provider_services s ON s.id=ss.service_id
                        WHERE {svc_where} AND ss.slot_date BETWEEN ? AND ? AND ss.status IN ('open','full','closed')''',(*svc_args,start,end)).fetchone()
    bk=db.execute(f'''SELECT COUNT(*) n, COALESCE(SUM(b.participants),0) divers, COALESCE(SUM(b.price),0) revenue,
                          COALESCE(SUM(CASE WHEN b.payment_status='paid' THEN b.price ELSE 0 END),0) paid,
                          COALESCE(SUM(CASE WHEN b.status IN ('pending','requested') THEN 1 ELSE 0 END),0) pending
                      FROM bookings b WHERE {bk_where} AND b.booking_date BETWEEN ? AND ? AND b.status NOT IN ('cancelled','rejected','expired','payment_in_progress')''',(*bk_args,start,end)).fetchone()
    cancelled=db.execute(f"SELECT COUNT(*) FROM bookings b WHERE {bk_where} AND b.booking_date BETWEEN ? AND ? AND b.status IN ('cancelled','rejected')",(*bk_args,start,end)).fetchone()[0]
    offered=int(slots['offered'] or 0); taken=int(slots['taken'] or 0)
    return {'slots':int(slots['n'] or 0),'offered':offered,'taken':taken,'free':max(offered-taken,0),
            'occupancy':round(100*taken/offered) if offered else 0,'bookings':int(bk['n'] or 0),'divers':int(bk['divers'] or 0),
            'revenue':round(float(bk['revenue'] or 0),2),'paid':round(float(bk['paid'] or 0),2),'pending':int(bk['pending'] or 0),'cancelled':int(cancelled or 0)}


def center_planning(db, user, month):
    svc_where,svc_args,bk_where,bk_args=planning_scope(user)
    first,last=_month_bounds(month); start,end=first.isoformat(),last.isoformat()
    rows=db.execute(f'''SELECT ss.id,ss.service_id,ss.slot_date,ss.slot_time,ss.spots_total,ss.spots_available,ss.status,
                               s.title AS service_title,s.color AS service_color,s.service_type,s.price AS service_price,s.currency,s.duration_minutes
                          FROM service_slots ss JOIN provider_services s ON s.id=ss.service_id
                         WHERE {svc_where} AND ss.slot_date BETWEEN ? AND ? AND ss.status IN ('open','full','closed')
                         ORDER BY ss.slot_date,ss.slot_time,s.title LIMIT 3000''',(*svc_args,start,end)).fetchall()
    slots=[]; by_id={}; tariff_cache={}; today_iso=_dt.date.today().isoformat()
    for r in rows:
        d=dict(r); d['taken']=max(int(d['spots_total'] or 0)-int(d['spots_available'] or 0),0); d['points']=[]; d['bookings']=[]
        if d['slot_date']>=today_iso:
            key=(d['service_id'],d['slot_date'])
            if key not in tariff_cache: tariff_cache[key]=effective_service_tariff(db,d['service_id'],d['slot_date'])[0]
            d['service_price']=tariff_cache[key]
        slots.append(d); by_id[d['id']]=d
    ids=list(by_id)
    for chunk in [ids[i:i+500] for i in range(0,len(ids),500)]:
        for pp in db.execute(f"SELECT sp.slot_id,p.id,p.name FROM service_slot_points sp JOIN dive_points p ON p.id=sp.dive_point_id WHERE sp.slot_id IN ({','.join('?'*len(chunk))}) ORDER BY p.name",chunk).fetchall():
            by_id[pp['slot_id']]['points'].append({'id':pp['id'],'name':pp['name']})
    other=[]
    for b in db.execute(f'''SELECT b.id,b.slot_id,b.service_id,b.booking_date,b.booking_time,b.participants,b.status,b.payment_status,b.price,b.booking_mode,
                                   b.response_deadline,b.payment_deadline,COALESCE(b.source,'online') AS source,COALESCE(b.contact_name,u.fullname) AS fullname,
                                   s.title AS service_title,s.color AS service_color,p.name AS point_name
                              FROM bookings b LEFT JOIN users u ON u.id=b.user_id LEFT JOIN provider_services s ON s.id=b.service_id
                              LEFT JOIN dive_points p ON p.id=b.dive_point_id
                             WHERE {bk_where} AND b.booking_date BETWEEN ? AND ? AND b.status<>'expired'
                             ORDER BY b.booking_date,b.booking_time,b.id LIMIT 5000''',(*bk_args,start,end)).fetchall():
        bd=dict(b)
        if bd['status']=='payment_in_progress':
            # Only a grey «pago en curso» placeholder: no name, no money, not a booking yet.
            bd={'id':None,'slot_id':bd['slot_id'],'service_id':bd['service_id'],'booking_date':bd['booking_date'],'booking_time':bd['booking_time'],
                'participants':bd['participants'],'status':'payment_in_progress','status_label':'Pago en curso','placeholder':True}
        else:
            bd.update(booking_view_status(b))
        if bd['slot_id'] in by_id: by_id[bd['slot_id']]['bookings'].append(bd)
        else: other.append(bd)
    # Twelve months around the one on screen, for the trend strip.
    t0=_shift_month(first,-6); t1=_shift_month(first,6)-_dt.timedelta(days=1)
    trend={}
    for r in db.execute(f'''SELECT substr(ss.slot_date,1,7) m, COUNT(*) n, SUM(ss.spots_total) offered, SUM(MAX(ss.spots_total-ss.spots_available,0)) taken
                              FROM service_slots ss JOIN provider_services s ON s.id=ss.service_id
                             WHERE {svc_where} AND ss.slot_date BETWEEN ? AND ? AND ss.status IN ('open','full','closed') GROUP BY m''',(*svc_args,t0.isoformat(),t1.isoformat())).fetchall():
        trend.setdefault(r['m'],{})['slots']=int(r['n'] or 0); trend[r['m']]['offered']=int(r['offered'] or 0); trend[r['m']]['taken']=int(r['taken'] or 0)
    for r in db.execute(f'''SELECT substr(b.booking_date,1,7) m, COUNT(*) n, SUM(b.participants) divers, SUM(b.price) revenue FROM bookings b
                             WHERE {bk_where} AND b.booking_date BETWEEN ? AND ? AND b.status NOT IN ('cancelled','rejected','expired','payment_in_progress') GROUP BY m''',(*bk_args,t0.isoformat(),t1.isoformat())).fetchall():
        e=trend.setdefault(r['m'],{}); e['bookings']=int(r['n'] or 0); e['divers']=int(r['divers'] or 0); e['revenue']=round(float(r['revenue'] or 0),2)
    months=[]
    for i in range(12):
        m=_shift_month(t0,i).isoformat()[:7]; e=trend.get(m,{})
        months.append({'month':m,'slots':e.get('slots',0),'offered':e.get('offered',0),'taken':e.get('taken',0),'bookings':e.get('bookings',0),'divers':e.get('divers',0),'revenue':e.get('revenue',0)})
    pf=_shift_month(first,-1); pl=first-_dt.timedelta(days=1)
    return {'month':start[:7],'start':start,'end':end,'today':_dt.date.today().isoformat(),
            'prev':pf.isoformat()[:7],'next':_shift_month(first,1).isoformat()[:7],
            'slots':slots,'other':other,'stats':_planning_figures(db,svc_where,svc_args,bk_where,bk_args,start,end),
            'prev_stats':_planning_figures(db,svc_where,svc_args,bk_where,bk_args,pf.isoformat(),pl.isoformat()),'trend':months}


def qr_matrix(payload):
    sys.path.insert(0, str(ROOT/'vendor'))
    import qrcode
    qr=qrcode.QRCode(box_size=1,border=0,error_correction=qrcode.constants.ERROR_CORRECT_M); qr.add_data(payload); qr.make(fit=True)
    return [''.join('1' if v else '0' for v in row) for row in qr.get_matrix()]


# ---------------------------------------------------------------------------
# Partners / sponsors band and sponsored offers on the home page (v50.26), managed by the administrator.
# ---------------------------------------------------------------------------
PROMO_KINDS=('partner','offer')
SPONSORED_LABEL='Patrocinado'  # fixed label of paid placements (Fase 2.10), translated on screen


def clean_promo_url(v):
    v=(clean_text(v,500) or '').strip()
    if not v: return ''
    if v.startswith('#/') or re.match(r'^https?://[^\s<>"]+$',v,re.I): return v
    if re.match(r'^[a-z0-9.-]+\.[a-z]{2,}(/[^\s<>"]*)?$',v,re.I): return 'https://'+v
    raise ValueError('El enlace debe empezar por https:// (o por #/ para una página de WORLDIVES).')


def _build_promos(db):
    rows=db.execute('SELECT id,kind,title,subtitle,label,url,image_path,starts_on,ends_on,sort_order FROM site_promos WHERE active=1 ORDER BY sort_order,id').fetchall()
    settings={r['key']:r['value'] for r in db.execute("SELECT key,value FROM site_settings WHERE key LIKE 'partners_%'").fetchall()}
    # Associated dive centers for the home band: those with their own logo first, then the ones with most activity.
    centers=[]
    for r in db.execute('''SELECT c.id,c.name,c.city,c.country,c.logo_url FROM centers c
                           LEFT JOIN (SELECT center_id, COUNT(*) n FROM provider_services WHERE active=1 GROUP BY center_id) sv ON sv.center_id=c.id
                           WHERE c.active=1
                           ORDER BY (CASE WHEN c.logo_url LIKE '/assets/%' THEN 0 ELSE 1 END), COALESCE(sv.n,0) DESC, c.name LIMIT 80''').fetchall():
        d=dict(r); logo=(d.pop('logo_url') or '').strip()
        d['logo']=logo if logo and not re.match(r'^https?://[^/]+/?$',logo) else ''
        centers.append(d)
    total=db.execute('SELECT COUNT(*) FROM centers WHERE active=1').fetchone()[0]
    return {'items':[dict(r) for r in rows],'settings':settings,'centers':centers,'center_total':total}


def public_promos(db):
    today=_dt.date.today().isoformat(); snap=PROMOS.get(db); st=snap.get('settings') or {}
    out={'partners':[],'offers':[],'centers':snap.get('centers') or [],'center_total':snap.get('center_total') or 0,'contact':{'email':st.get('partners_email') or '','text':st.get('partners_text') or ''}}
    for p in snap['items']:
        if (p['starts_on'] and p['starts_on']>today) or (p['ends_on'] and p['ends_on']<today): continue
        if p['kind']=='offer' and not p['image_path']: continue
        out['partners' if p['kind']=='partner' else 'offers'].append(dict(p,label=SPONSORED_LABEL))
    return out


def invalidate_after_post(path):
    """Catalogue edits show up at once in this process (other worker processes refresh within a minute)."""
    for prefix,*names in SNAPSHOT_WRITE_PREFIXES:
        if path.startswith(prefix):
            for n in names: globals()[n].invalidate()


POINTS=Snapshot('points',_build_points)
DIRECTORY=Snapshot('directory',_build_directory)
DIVE_TYPES=Snapshot('dive-types',_build_dive_types)
TRAVEL=Snapshot('travel',_build_travel)
SITE_MEDIA=Snapshot('site-media',_build_site_media)
PROMOS=Snapshot('promos',_build_promos)


def ensure_reward_event(db, user_id, event_key, title, description, points=0, wallet_amount=0.0):
    row = db.execute('SELECT id FROM reward_events WHERE user_id=? AND event_key=?', (user_id, event_key)).fetchone()
    if row:
        return False
    db.execute('INSERT INTO reward_events(user_id,event_key,title,description,points,wallet_amount,created_at) VALUES(?,?,?,?,?,?,?)',
               (user_id, event_key, title, description, int(points or 0), float(wallet_amount or 0), now()))
    db.execute('INSERT INTO rewards(user_id,title,description,points,completed,created_at) VALUES(?,?,?,?,1,?)',
               (user_id, title, description, int(points or 0), now()))
    if float(wallet_amount or 0):
        db.execute('INSERT INTO wallet_transactions(user_id,amount,description,created_at) VALUES(?,?,?,?)',
                   (user_id, float(wallet_amount), title, now()))
    return True


def sync_user_rewards(db, user_id):
    """Automatically award lightweight rewards for actions the diver already performs."""
    profile = db.execute('SELECT * FROM user_profiles WHERE user_id=?', (user_id,)).fetchone()
    user = db.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()
    if not user:
        return
    # Profile completion is intentionally simple: no daily check-in or artificial engagement.
    if profile and profile['phone'] and profile['city'] and profile['certification_id']:
        ensure_reward_event(db, user_id, 'profile_complete', 'Perfil preparado',
                            'Has completado los datos esenciales de tu perfil de buceador.', 50, 0)
    dives = db.execute('SELECT id FROM logbook_entries WHERE user_id=? ORDER BY id', (user_id,)).fetchall()
    dive_count = len(dives)
    # Every real logbook entry gives a modest amount of progression; no monetary credit per dive.
    for i, dive in enumerate(dives, 1):
        ensure_reward_event(db, user_id, f'logbook:dive:{dive[0]}', 'Inmersión registrada',
                            'Has añadido una inmersión a tu Log Book.', 10, 0)
    milestones = [
        (1, 'first_dive', 'Primera inmersión', 'Tu primera inmersión queda registrada en WORLDIVES.', 50, 0),
        (5, 'dives_5', '5 inmersiones', 'Cinco inmersiones registradas en tu Log Book.', 100, 0),
        (10, 'dives_10', '10 inmersiones', 'Diez inmersiones registradas.', 150, 0),
        (25, 'dives_25', '25 inmersiones', 'Has alcanzado 25 inmersiones.', 300, 0),
        (50, 'dives_50', '50 inmersiones', 'Has alcanzado 50 inmersiones.', 600, 0),
        (100, 'dives_100', '100 inmersiones', 'Has alcanzado 100 inmersiones.', 1200, 0),
    ]
    for target,key,title,desc,pts,wallet in milestones:
        if dive_count >= target:
            ensure_reward_event(db, user_id, key, title, desc, pts, wallet)
    # Documents: only one modest bonus per useful document type.
    for doc_type, label in [('Titulación','Titulación guardada'), ('Seguro','Seguro guardado'), ('Certificado médico','Certificado médico guardado')]:
        if db.execute('SELECT 1 FROM user_documents WHERE user_id=? AND lower(document_type)=lower(?) LIMIT 1', (user_id, doc_type)).fetchone():
            ensure_reward_event(db, user_id, 'document:'+doc_type.lower(), label,
                                'Has preparado documentación útil para reservar con tranquilidad.', 25, 0)
    # Completed reservations are valuable but not spammy.
    bookings = db.execute("SELECT id FROM bookings WHERE user_id=? AND status='completed' ORDER BY id", (user_id,)).fetchall()
    for b in bookings:
        ensure_reward_event(db, user_id, f'booking:completed:{b[0]}', 'Inmersión completada con un centro',
                            'Has completado una reserva de buceo.', 40, 0)
    # Visiting a center through its QR is rewarded once per center.
    centers = db.execute('SELECT center_id FROM center_links WHERE user_id=? GROUP BY center_id', (user_id,)).fetchall()
    for c in centers:
        ensure_reward_event(db, user_id, f'center:visit:{c[0]}', 'Centro visitado',
                            'Has hecho check-in en un centro de buceo.', 20, 0)


def reward_level(total_points):
    levels = [(0,'Explorador'),(250,'Buceador'),(750,'Explorador del mundo'),(1500,'Navegante'),(3000,'Embajador WORLDIVES'),(6000,'Leyenda')]
    current=levels[0]
    nxt=None
    for item in levels:
        if total_points >= item[0]: current=item
        elif nxt is None: nxt=item
    return {'name':current[1], 'threshold':current[0], 'next_threshold':nxt[0] if nxt else None, 'next_name':nxt[1] if nxt else None}


def reward_offer_row(row):
    d=dict(row)
    return d


# ---------------------------------------------------------------------------
# Online payments (v50.29): one place decides whether a centre can take card payments and
# one function confirms a payment, whoever reports it first (Stripe webhook, return page or sweeper).
# ---------------------------------------------------------------------------
def stripe_secret():
    return os.environ.get('STRIPE_SECRET_KEY','').strip()


def stripe_module():
    """The Stripe library configured with the secret key. WOD_STRIPE_API_BASE points it to a local simulator in tests."""
    import stripe
    stripe.api_key = stripe_secret()
    base = os.environ.get('WOD_STRIPE_API_BASE', '').strip()
    if base: stripe.api_base = base
    return stripe


def center_payments_ready(center):
    """True when WORLDIVES can charge cards for this centre: platform keys + a finished Stripe Connect account."""
    if not center or not stripe_secret(): return False
    keys=center.keys() if hasattr(center,'keys') else center
    return bool(('stripe_account_id' in keys and center['stripe_account_id']) and int(center['stripe_charges_enabled'] or 0) and int(center['stripe_payouts_enabled'] or 0))


def _obj(o,k,default=None):
    try:
        if isinstance(o,dict): return o.get(k,default)
        if isinstance(o,sqlite3.Row): return o[k] if k in o.keys() else default
        return getattr(o,k,default)
    except Exception: return default


def finalize_paid_order(db, order, session, source):
    """Marks a payment order as paid after checking the amount, confirms its booking and keeps the spots.
    Idempotent: calling it twice changes nothing. Returns (ok, message)."""
    if order['status']=='paid': return True,'already'
    pay_status=_obj(session,'payment_status'); total=_obj(session,'amount_total'); cur=(_obj(session,'currency') or '').upper()
    expected=int(round(float(order['amount'] or 0)*100))
    if pay_status not in ('paid','no_payment_required'): return False,'not_paid'
    if total is not None and int(total)!=expected or (cur and cur!=(order['currency'] or 'EUR').upper()):
        db.execute("UPDATE payment_orders SET status='review',updated_at=? WHERE id=?",(now(),order['id']))
        if order['booking_id']: db.execute("UPDATE bookings SET payment_status='review',updated_at=? WHERE id=? AND payment_status<>'paid'",(now(),order['booking_id']))
        audit(db,order['user_id'],'payment_amount_mismatch','payment_order',order['id'],{'expected':expected,'received':total,'currency':cur,'source':source})
        if order['booking_id']: notify_booking(db,order['booking_id'],'payment_review')
        return False,'mismatch'
    receipt=brand=last4=None
    pi=_obj(session,'payment_intent'); pi_id=pi if isinstance(pi,str) else _obj(pi,'id')
    if pi and not isinstance(pi,str):
        ch=_obj(pi,'latest_charge')
        if ch and not isinstance(ch,str):
            receipt=_obj(ch,'receipt_url'); card=_obj(_obj(ch,'payment_method_details') or {},'card') or {}
            brand=_obj(card,'brand'); last4=_obj(card,'last4')
    received=(int(total)/100 if total is not None else float(order['amount'] or 0))
    db.execute("UPDATE payment_orders SET status='paid',provider_payment_id=COALESCE(?,provider_payment_id),payment_intent_id=COALESCE(?,payment_intent_id),paid_at=?,amount_received=?,receipt_url=COALESCE(?,receipt_url),card_brand=COALESCE(?,card_brand),card_last4=COALESCE(?,card_last4),updated_at=? WHERE id=?",
               (_obj(session,'id'),pi_id,now(),received,receipt,brand,last4,now(),order['id']))
    deposit=(order['payment_kind'] if 'payment_kind' in order.keys() else 'full')=='deposit'
    if order['booking_id']:
        b=db.execute('SELECT * FROM bookings WHERE id=?',(order['booking_id'],)).fetchone()
        if b:
            reserved=int(b['slot_reserved'] or 0); st=wbk.normalize_state(b['status'])
            was_visible=st in ('requested','accepted_pending_payment','confirmed')
            late=st in ('expired','cancelled','rejected')
            if b['slot_id'] and not reserved:
                # The hold was released (late payment): take the spots again if they are still there.
                if reserve_slot_spots(db,b['slot_id'],max(1,int(b['participants'] or 1))): reserved=1
                else:
                    # No spots left for a late payment: never a phantom booking. The payment goes to review/refund.
                    db.execute("UPDATE payment_orders SET status='review',updated_at=? WHERE id=?",(now(),order['id']))
                    db.execute("UPDATE bookings SET payment_status='review',updated_at=? WHERE id=?",(now(),b['id']))
                    audit(db,order['user_id'],'payment_after_slot_full','booking',b['id'],{'source':source})
                    notify_booking(db,b['id'],'payment_review')
                    return False,'late_no_spots'
            # A payment confirmed by Stripe is the ONLY way a «Pago al reservar» booking becomes confirmed.
            paid_total=round(float(b['amount_paid'] or 0)+received,2); due=round(max(0.0,float(b['price'] or 0)-paid_total),2)
            db.execute("UPDATE bookings SET payment_status=?,amount_paid=?,amount_due=?,status=CASE WHEN status IN ('pending','requested','payment_in_progress','accepted_pending_payment','confirmed','expired') THEN 'confirmed' ELSE status END,confirmed_at=COALESCE(confirmed_at,?),slot_reserved=?,expired_reason=NULL,updated_at=? WHERE id=?",
                       ('deposit_paid' if deposit and due>0 else 'paid',paid_total,due,now(),reserved,now(),b['id']))
            body=(f'Hemos recibido la señal de {received:.2f} {order["currency"] or "EUR"}. Tu reserva #{b["id"]} está confirmada; el resto ({due:.2f} {order["currency"] or "EUR"}) se paga en el centro.'
                  if deposit and due>0 else f'Hemos recibido tu pago de {received:.2f} {order["currency"] or "EUR"}. Tu reserva #{b["id"]} está confirmada.')
            db.execute("INSERT INTO messages(sender_user_id,recipient_user_id,booking_id,subject,body,created_at,kind) VALUES(?,?,?,?,?,?,'system')",(order['provider_user_id'] or b['user_id'],b['user_id'],b['id'],'Pago recibido · reserva confirmada',body,now()))
            notify_booking(db,b['id'],'paid',{'was_confirmed':st=='accepted_pending_payment' or (was_visible and st=='confirmed'),'late':late})
    if order['experience_booking_id']:
        db.execute("UPDATE experience_bookings SET status='confirmed',payment_status='paid',amount_paid=COALESCE(amount_paid,0)+?,updated_at=? WHERE id=?",(received,now(),order['experience_booking_id']))
    audit(db,order['user_id'],'payment_completed','payment_order',order['id'],{'provider':'stripe','source':source})
    return True,'paid'


def release_order_hold(db, order, new_status):
    """A Checkout ended without payment. «Pago al reservar»: the booking expires and its spots are freed at once
    (it never existed for the centre). «Bajo petición» accepted: the spots stay held until the payment deadline."""
    db.execute('UPDATE payment_orders SET status=?,updated_at=? WHERE id=?',(new_status,now(),order['id']))
    if order['booking_id']:
        b=db.execute('SELECT * FROM bookings WHERE id=?',(order['booking_id'],)).fetchone()
        if not b or b['payment_status']=='paid': return
        if wbk.normalize_state(b['status'])=='payment_in_progress':
            expire_checkout(order)
            release_booking_spots(db,b)
            db.execute("UPDATE bookings SET status='expired',expired_reason=?,payment_status='not_paid',updated_at=? WHERE id=?",('payment_cancelled' if new_status=='cancelled' else 'hold_expired',now(),b['id']))
        elif wbk.normalize_state(b['status'])=='accepted_pending_payment':
            db.execute("UPDATE bookings SET payment_status='required',updated_at=? WHERE id=?",(now(),b['id']))


def sweep_payment_orders():
    """Every few minutes: confirm payments whose webhook never arrived and free the spots of abandoned checkouts."""
    while True:
        time.sleep(300)
        db=None
        try:
            db=connect(); limit=datetime.now(timezone.utc).timestamp()-40*60
            for o in db.execute("SELECT * FROM payment_orders WHERE status='pending' ORDER BY id LIMIT 200").fetchall():
                try: created=datetime.fromisoformat(o['created_at']).timestamp()
                except Exception: continue
                if created>limit: continue
                done=False
                if stripe_secret() and o['provider_payment_id']:
                    try:
                        sess=stripe_session(o)
                        if _obj(sess,'payment_status')=='paid': finalize_paid_order(db,o,sess,'sweeper'); done=True
                        elif _obj(sess,'status')=='open': expire_checkout(o)
                    except Exception as exc: sys.stderr.write(f'[pagos] no se pudo revisar el pedido {o["id"]}: {exc}\n')
                if not done: release_order_hold(db,o,'expired')
                db.commit()
        except Exception as exc:
            sys.stderr.write(f'[pagos] revisión periódica: {exc}\n')
        finally:
            if db: db.close()


# ---------------------------------------------------------------------------
# Automatic emails (v50.30)
# Every email is rendered at the moment of the event (in the recipient's language) and stored in
# email_outbox inside the same transaction as the change that caused it. A background sender
# delivers the queue through SMTP (WOD_SMTP_*). Without SMTP configured nothing is lost: emails
# wait in the outbox and the administrator can read them in Administración → Correos.
# ---------------------------------------------------------------------------
import smtplib as _smtplib
from email.message import EmailMessage as _EmailMessage
from email.utils import formataddr as _formataddr, make_msgid as _make_msgid
from datetime import timedelta as _timedelta

# The 10 languages of the site (v50.33). Retired: ja, ko → en and zt → zh (see normalize_lang).
MAIL_LANGS = ('es', 'en', 'fr', 'de', 'it', 'pt', 'pl', 'nl', 'zh', 'ru')
HTML_LANG = {'zh': 'zh-Hans'}
_EMAIL_I18N = {}


def email_i18n(lang):
    """Translations of the email texts (Spanish source → language), kept in app/emails/<lang>.json."""
    if lang in _EMAIL_I18N: return _EMAIL_I18N[lang]
    d = {}
    try:
        p = ROOT / 'app' / 'emails' / f'{lang}.json'
        if lang != 'es' and p.exists(): d = json.loads(p.read_text(encoding='utf-8'))
    except Exception as exc:
        sys.stderr.write(f'[correo] traducciones {lang}: {exc}\n')
    _EMAIL_I18N[lang] = d
    return d


class _SafeDict(dict):
    def __missing__(self, key): return ''


def mail_t(lang, text, **kw):
    s = email_i18n(lang).get(text, text) if lang and lang != 'es' else text
    try: return s.format_map(_SafeDict(kw))
    except Exception:
        try: return text.format_map(_SafeDict(kw))
        except Exception: return text


def public_site_url():
    return (os.environ.get('WOD_PUBLIC_URL', '').strip() or f'http://localhost:{PORT}').rstrip('/')


def smtp_config():
    host = os.environ.get('WOD_SMTP_HOST', '').strip()
    site_host = urlparse(public_site_url()).hostname or ''
    default_from = f'no-reply@{site_host}' if '.' in site_host and not site_host.replace('.', '').isdigit() else 'no-reply@worldives.local'
    try: port = int(os.environ.get('WOD_SMTP_PORT', '587') or 587)
    except ValueError: port = 587
    return {'host': host, 'port': port,
            'user': os.environ.get('WOD_SMTP_USER', '').strip(), 'password': os.environ.get('WOD_SMTP_PASSWORD', ''),
            'security': (os.environ.get('WOD_SMTP_SECURITY', 'starttls') or 'starttls').strip().lower(),
            'from': os.environ.get('WOD_MAIL_FROM', '').strip() or default_from,
            'from_name': os.environ.get('WOD_MAIL_FROM_NAME', 'WORLDIVES DISCOVERY').strip() or 'WORLDIVES DISCOVERY',
            'reply_to': os.environ.get('WOD_MAIL_REPLY_TO', '').strip(), 'enabled': bool(host)}


def legal_settings(db):
    rows = {r['key']: r['value'] for r in db.execute("SELECT key,value FROM site_settings WHERE key LIKE 'legal\\_%' ESCAPE '\\'").fetchall()}
    return {k[6:]: (v or '').strip() for k, v in rows.items()}


_MONTHS = {
    'en': ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
    'fr': ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'],
    'de': ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'],
    'it': ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre'],
    'pt': ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'],
    'nl': ['januari', 'februari', 'maart', 'april', 'mei', 'juni', 'juli', 'augustus', 'september', 'oktober', 'november', 'december'],
    'pl': ['stycznia', 'lutego', 'marca', 'kwietnia', 'maja', 'czerwca', 'lipca', 'sierpnia', 'września', 'października', 'listopada', 'grudnia'],
    'ru': ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']}
_DAYS = {
    'en': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
    'fr': ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche'],
    'de': ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag'],
    'it': ['lunedì', 'martedì', 'mercoledì', 'giovedì', 'venerdì', 'sabato', 'domenica'],
    'pt': ['segunda-feira', 'terça-feira', 'quarta-feira', 'quinta-feira', 'sexta-feira', 'sábado', 'domingo'],
    'nl': ['maandag', 'dinsdag', 'woensdag', 'donderdag', 'vrijdag', 'zaterdag', 'zondag'],
    'zh': ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日'],
    'pl': ['poniedziałek', 'wtorek', 'środa', 'czwartek', 'piątek', 'sobota', 'niedziela'],
    'ru': ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье']}


def mail_date(value, lang='es'):
    """Long date in the recipient's language («domingo, 11 de octubre de 2026», «Sunday 11 October 2026»…)."""
    try: d = _dt.date.fromisoformat(str(value)[:10])
    except Exception: return str(value or '')
    if lang == 'es': return es_long_date(d.isoformat())
    if lang == 'en': return f"{_DAYS['en'][d.weekday()]} {d.day} {_MONTHS['en'][d.month - 1]} {d.year}"
    if lang == 'de': return f"{_DAYS['de'][d.weekday()]}, {d.day}. {_MONTHS['de'][d.month - 1]} {d.year}"
    if lang in ('fr', 'it', 'nl'): return f"{_DAYS[lang][d.weekday()]} {d.day} {_MONTHS[lang][d.month - 1]} {d.year}"
    if lang == 'pt': return f"{_DAYS['pt'][d.weekday()]}, {d.day} de {_MONTHS['pt'][d.month - 1]} de {d.year}"
    if lang in ('pl', 'ru'): return f"{_DAYS[lang][d.weekday()]}, {d.day} {_MONTHS[lang][d.month - 1]} {d.year}" + (' г.' if lang == 'ru' else ' r.')
    if lang == 'zh': return f"{d.year}年{d.month}月{d.day}日 {_DAYS['zh'][d.weekday()]}"
    return d.strftime('%d/%m/%Y')


def mail_datetime(value, lang='es'):
    """«domingo, 11 de octubre de 2026, 18:30» in the recipient's language (deadlines)."""
    if not value: return ''
    try: d = datetime.fromisoformat(str(value))
    except ValueError: return str(value)
    return f"{mail_date(d.date().isoformat(), lang)}, {d.strftime('%H:%M')}"


def mail_money(amount, currency='EUR', lang='es'):
    cur = (currency or 'EUR').upper(); sym = {'EUR': '€', 'USD': '$', 'GBP': '£'}.get(cur)
    v = float(amount or 0)
    if lang in ('en', 'zh'):
        txt = f'{v:,.2f}'.removesuffix('.00')
        return f'{sym}{txt}' if sym else f'{txt} {cur}'
    if lang in ('pl', 'ru'):  # 1 234,50 €  (narrow no-break space as thousands separator)
        txt = f'{v:,.2f}'.replace(',', '\u202f').replace('.', ',').removesuffix(',00')
        return f'{txt} {sym}' if sym else f'{txt} {cur}'
    txt = f'{v:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.').removesuffix(',00')
    return f'{txt} {sym}' if sym else f'{txt} {cur}'


def user_lang(db, user_id):
    r = db.execute('SELECT preferred_language FROM user_profiles WHERE user_id=?', (user_id,)).fetchone()
    return normalize_lang((r['preferred_language'] if r else '') or 'es')


def mail_deliverable(email):
    e = str(email or '').strip().lower()
    return bool(re.fullmatch(r'[^@\s]+@[^@\s]+\.[a-z]{2,}', e)) and not e.endswith('.local') and not e.endswith('.test') and not e.endswith('@example.com')


# Templates: subject + preheader + blocks. Texts are Spanish sources with {placeholders}, translated per language.
# Blocks: h (title), p (paragraph), note (highlighted box), list (items), code (big text), details (booking table),
# payment (payment line), policy (cancellation policy), bring (checklist), diver (client data for centres),
# button (label, url key), agenda (centre daily list).
EMAIL_TEMPLATES = {
 'welcome': {'to': 'diver', 'subject': 'Bienvenido a WORLDIVES DISCOVERY', 'pre': 'Tu cuenta está lista para buscar y reservar inmersiones.', 'blocks': [
   ('h', '¡Hola, {first_name}! Ya formas parte de WORLDIVES'),
   ('p', 'Tu cuenta está lista. Desde ahora puedes buscar puntos de buceo de todo el mundo, reservar con centros de buceo y llevar tu Log Book en un solo sitio.'),
   ('list', ['Completa tu ficha de buceador una sola vez: los centros reciben tu titulación y tus tallas al reservar.',
             'Sube tu titulación y tu seguro para reservar más rápido.',
             'Cada inmersión suma puntos y desbloquea recompensas.']),
   ('button', ('Completar mi ficha', 'account_url'))]},
 'welcome_pro': {'to': 'pro', 'subject': 'Tu cuenta profesional en WORLDIVES DISCOVERY', 'pre': 'Siguientes pasos para empezar a recibir reservas.', 'blocks': [
   ('h', 'Bienvenido, {first_name}'),
   ('p', 'Hemos recibido el alta de tu cuenta profesional. Revisaremos tus datos para activarla y marcar tu perfil como verificado. Mientras tanto, estos son los siguientes pasos:'),
   ('list', ['Completa tu escaparate: fotos, descripción, idiomas y datos de contacto.',
             'Crea tus servicios y tarifas y programa tus salidas en el planning.',
             'Activa los cobros online en «Cobros y pagos» para cobrar al reservar.',
             'Elige tu política de cancelación para que los buceadores la vean antes de reservar.']),
   ('button', ('Abrir mi panel', 'panel_url'))]},
 'password_reset': {'to': 'any', 'subject': 'Restablece tu contraseña de WORLDIVES', 'pre': 'El enlace caduca en 1 hora.', 'blocks': [
   ('h', 'Restablecer contraseña'),
   ('p', 'Hola {first_name}, hemos recibido una solicitud para cambiar la contraseña de tu cuenta de WORLDIVES.'),
   ('button', ('Elegir una contraseña nueva', 'reset_url')),
   ('note', 'El enlace caduca en 1 hora y solo se puede usar una vez. Si no has sido tú, ignora este correo: tu contraseña no cambiará.')]},
 'password_changed': {'to': 'any', 'subject': 'Tu contraseña se ha cambiado', 'pre': 'Aviso de seguridad de tu cuenta.', 'blocks': [
   ('h', 'Contraseña cambiada'),
   ('p', 'Hola {first_name}, la contraseña de tu cuenta de WORLDIVES se ha cambiado el {when}. Por seguridad hemos cerrado las demás sesiones abiertas.'),
   ('note', 'Si no has sido tú, restablece tu contraseña ahora y escríbenos.'),
   ('button', ('Restablecer contraseña', 'forgot_url'))]},
 'booking_request': {'to': 'diver', 'subject': 'Solicitud enviada: {service} · {date_short}', 'pre': '{center} responderá antes de {response_deadline}.', 'blocks': [
   ('h', 'Hemos enviado tu solicitud'),
   ('p', 'Hola {first_name}, {center} ha recibido tu solicitud ({mode_label}). Te avisaremos por correo en cuanto la acepte o la rechace, y como muy tarde el {response_deadline}.'),
   ('details', None), ('note', '{pay_note}'), ('policy', None), ('button', ('Ver mi reserva', 'booking_url'))]},
 'booking_confirmed': {'to': 'diver', 'subject': 'Reserva confirmada: {service} · {date_short}', 'pre': 'Tu plaza con {center} está confirmada.', 'blocks': [
   ('h', '¡Tu reserva está confirmada!'),
   ('p', 'Hola {first_name}, {center} te espera. Aquí tienes todos los detalles de tu reserva.'),
   ('details', None), ('payment', None), ('button', ('Ver mi reserva y el QR', 'booking_url')),
   ('p', 'Descarga el comprobante en PDF para tenerlo sin conexión: {pdf_url}'), ('policy', None), ('bring', None)]},
 'booking_manual': {'to': 'diver', 'subject': 'Tu reserva con {center}: {service} · {date_short}', 'pre': '{center} ha registrado tu reserva.', 'blocks': [
   ('h', 'Tienes una reserva con {center}'),
   ('p', 'Hola {first_name}, {center} ha registrado esta reserva a tu nombre en WORLDIVES. Si no la reconoces, contacta directamente con el centro.'),
   ('details', None), ('payment', None), ('bring', None), ('p', 'Comprobante en PDF: {pdf_url}')]},
 'payment_required': {'to': 'diver', 'subject': 'Plaza aceptada: completa el pago · {service}', 'pre': 'Paga antes de {payment_deadline}.', 'blocks': [
   ('h', 'Tu plaza está aceptada'),
   ('p', 'Hola {first_name}, {center} ha aceptado tu solicitud y te guarda la plaza. Completa el pago de {total} antes del {payment_deadline} para confirmar la reserva.'),
   ('note', 'Si no pagas antes de ese momento, la reserva se cancela sola y las plazas se liberan. No se te cobrará nada.'),
   ('details', None), ('button', ('Pagar ahora de forma segura', 'booking_url')),
   ('note', 'El pago lo procesa Stripe con cifrado y verificación 3D Secure. WORLDIVES y el centro nunca ven los datos de tu tarjeta.'), ('policy', None)]},
 'payment_receipt': {'to': 'diver', 'subject': 'Recibo de pago · {service} · {total}', 'pre': 'Hemos recibido tu pago.', 'blocks': [
   ('h', 'Pago recibido'),
   ('p', 'Hola {first_name}, hemos recibido tu pago. Tu reserva con {center} está confirmada.'),
   ('details', None), ('payment', None), ('button', ('Ver mi reserva y el QR', 'booking_url')), ('policy', None)]},
 'payment_review': {'to': 'diver', 'subject': 'Estamos revisando tu pago · {service}', 'pre': 'No pagues otra vez.', 'blocks': [
   ('h', 'Estamos revisando tu pago'),
   ('p', 'Hola {first_name}, el importe recibido no coincide con el de tu reserva con {center}. Nuestro equipo lo está revisando y te escribirá en breve.'),
   ('note', 'No hace falta que pagues otra vez. Si se ha cobrado de más, te lo devolveremos íntegramente.'),
   ('button', ('Ver mi reserva', 'booking_url'))]},
 'booking_rejected': {'to': 'diver', 'subject': 'Solicitud no disponible · {service} · {date_short}', 'pre': '{center} no puede atender esta solicitud.', 'blocks': [
   ('h', 'Esta solicitud no está disponible'),
   ('p', 'Hola {first_name}, lo sentimos: {center} no puede atender tu solicitud para el {date}.'),
   ('p', '{reject_reason_text}'),
   ('note', '{refund_note}'), ('button', ('Buscar otra fecha', 'center_url'))]},
 'booking_expired': {'to': 'diver', 'subject': 'Reserva caducada · {service} · {date_short}', 'pre': 'No se te ha cobrado nada.', 'blocks': [
   ('h', 'Tu reserva ha caducado'),
   ('p', 'Hola {first_name}, {expired_text}'),
   ('details', None), ('button', ('Buscar otra fecha', 'center_url'))]},
 'booking_cancelled_center': {'to': 'diver', 'subject': 'Reserva cancelada por el centro · {service}', 'pre': '{refund_short}', 'blocks': [
   ('h', '{center} ha cancelado tu reserva'),
   ('p', 'Hola {first_name}, el centro ha tenido que cancelar tu reserva del {date}. Suele deberse al estado del mar o a motivos de seguridad.'),
   ('details', None), ('note', '{refund_note}'), ('button', ('Buscar otra fecha', 'center_url'))]},
 'booking_cancelled_diver': {'to': 'diver', 'subject': 'Has cancelado tu reserva · {service}', 'pre': '{refund_short}', 'blocks': [
   ('h', 'Reserva cancelada'),
   ('p', 'Hola {first_name}, hemos cancelado tu reserva con {center} del {date}.'),
   ('details', None), ('note', '{refund_note}'), ('button', ('Buscar otra inmersión', 'search_url'))]},
 'reminder': {'to': 'diver', 'subject': 'Mañana buceas con {center} · {time}', 'pre': 'Todo lo que necesitas para mañana.', 'blocks': [
   ('h', '¡Mañana buceas!'),
   ('p', 'Hola {first_name}, te recordamos tu inmersión de mañana con {center}.'),
   ('details', None), ('bring', None), ('button', ('Ver mi reserva y el QR', 'booking_url')),
   ('p', 'Si no puedes acudir, cancela o avisa al centro cuanto antes desde tu reserva.')]},
 'review_request': {'to': 'diver', 'subject': '¿Qué tal con {center}?', 'pre': 'Tu opinión ayuda a otros buceadores.', 'blocks': [
   ('h', '¿Qué tal tu inmersión?'),
   ('p', 'Hola {first_name}, esperamos que disfrutaras buceando con {center}. ¿Nos cuentas qué tal? Tu reseña aparece como verificada y ayuda a otros buceadores a elegir.'),
   ('button', ('Escribir mi reseña', 'review_url')),
   ('p', 'Recuerda que puedes apuntar la profundidad, el tiempo y tus notas en tu Log Book.')]},
 'promotion_received': {'to': 'diver', 'subject': 'Tienes una promoción de {center}', 'pre': '{promo_title}', 'blocks': [
   ('h', 'Tienes una promoción'),
   ('p', 'Hola {first_name}, {center} te ha regalado una promoción:'), ('code', '{promo_title}'), ('p', '{promo_value}'),
   ('p', 'Válida hasta el {valid_until}. Enseña tu QR personal en el centro y lo validarán al momento.'),
   ('button', ('Ver mi QR', 'promo_url'))]},
 'experience_request': {'to': 'diver', 'subject': 'Solicitud enviada: {experience}', 'pre': 'El organizador te responderá en breve.', 'blocks': [
   ('h', 'Hemos enviado tu solicitud'),
   ('p', 'Hola {first_name}, el organizador de «{experience}» ha recibido tu solicitud para {participants} personas. Te avisaremos en cuanto responda.'),
   ('button', ('Ver mis viajes', 'area_url'))]},
 'experience_status': {'to': 'diver', 'subject': '{status_title}: {experience}', 'pre': '{status_title}', 'blocks': [
   ('h', '{status_title}'), ('p', 'Hola {first_name}, {status_text}'), ('button', ('Ver mis viajes', 'area_url'))]},
 'account_deleted': {'to': 'any', 'subject': 'Tu cuenta de WORLDIVES se ha eliminado', 'pre': 'Confirmación de baja.', 'blocks': [
   ('h', 'Cuenta eliminada'),
   ('p', 'Hola {first_name}, hemos eliminado tu cuenta y tus datos personales como nos pediste. Solo conservamos, de forma bloqueada, lo que la ley nos obliga a guardar (por ejemplo, los datos de los pagos).'),
   ('p', 'Gracias por haber buceado con nosotros. Si algún día quieres volver, estaremos aquí.')]},
 # ---- dive centres and professionals
 'center_new_booking': {'to': 'center', 'subject': 'Nueva reserva: {service} · {date_short} · {diver_name}', 'pre': '{action_short}', 'blocks': [
   ('h', '{action_title}'), ('p', '{diver_name} ha reservado «{service}» para el {date}.'),
   ('details', None), ('payment', None), ('diver', None), ('button', ('{action_button}', 'panel_booking_url'))]},
 'center_booking_expired': {'to': 'center', 'subject': 'Reserva caducada: {service} · {date_short} · {diver_name}', 'pre': '{status_label}', 'blocks': [
   ('h', 'Reserva caducada'), ('p', '{expired_text}'), ('details', None), ('button', ('Ver el planning', 'panel_planning_url'))]},
 'center_payments_disabled': {'to': 'center', 'subject': 'Tus servicios con «Pago al reservar» no se pueden reservar', 'pre': 'Los cobros online de tu centro no están activos.', 'blocks': [
   ('h', 'Revisa el modo de reserva de tus servicios'),
   ('p', 'Los cobros online de tu centro no están activos ahora mismo. Estos servicios usan «Pago al reservar» y han dejado de poder reservarse: {services}.'),
   ('p', 'Para que los buceadores puedan volver a reservarlos, reactiva los cobros en «Cobros y pagos» o cambia esos servicios a «Bajo petición». Las reservas ya confirmadas no cambian.'),
   ('button', ('Revisar mis servicios', 'panel_url'))]},
 'center_booking_paid': {'to': 'center', 'subject': 'Pago recibido: {service} · {date_short} · {diver_name}', 'pre': '{total} cobrados online.', 'blocks': [
   ('h', 'Pago recibido'), ('p', '{diver_name} ha pagado su reserva. La plaza queda confirmada.'),
   ('details', None), ('payment', None), ('button', ('Ver la reserva', 'panel_booking_url'))]},
 'center_booking_cancelled': {'to': 'center', 'subject': 'Reserva cancelada por el cliente: {service} · {date_short}', 'pre': '{diver_name} ha cancelado.', 'blocks': [
   ('h', 'Reserva cancelada por el cliente'),
   ('p', '{diver_name} ha cancelado su reserva del {date}. Las plazas vuelven a estar disponibles en tu planning.'),
   ('details', None), ('note', '{center_refund_note}'), ('button', ('Ver el planning', 'panel_planning_url'))]},
 'center_daily_agenda': {'to': 'center', 'subject': 'Agenda de mañana · {date_short} · {slots_count} salidas', 'pre': '{divers_count} buceadores confirmados.', 'blocks': [
   ('h', 'Tu agenda de mañana'), ('p', 'Estas son tus salidas del {date}:'), ('agenda', None),
   ('button', ('Abrir el planning', 'panel_planning_url'))]},
 'center_promo_invite': {'to': 'center', 'subject': '{issuer} te invita a una promoción', 'pre': '{promo_title}', 'blocks': [
   ('h', 'Invitación a una promoción'),
   ('p', '{issuer} quiere que su promoción «{promo_title}» también sea válida en tu centro. Si la aceptas, podrás validar y canjear los códigos de sus clientes.'),
   ('button', ('Ver la invitación', 'panel_qr_url'))]},
 'center_experience_request': {'to': 'center', 'subject': 'Nueva solicitud: {experience}', 'pre': '{diver_name} quiere apuntarse.', 'blocks': [
   ('h', 'Nueva solicitud de viaje'), ('p', '{diver_name} ha solicitado plaza en «{experience}» para {participants} personas.'),
   ('p', '{notes}'), ('button', ('Responder la solicitud', 'panel_exp_url'))]},
 'center_verified': {'to': 'center', 'subject': 'Tu perfil profesional está verificado en WORLDIVES', 'pre': 'Ya puedes recibir reservas.', 'blocks': [
   ('h', '¡Perfil verificado!'),
   ('p', 'Hola {first_name}, hemos verificado tu perfil profesional ({center}). Desde ahora puedes gestionar tus servicios y recibir reservas en WORLDIVES.'),
   ('button', ('Abrir mi panel', 'panel_url'))]},
 # ---- administrators
 'admin_new_pro': {'to': 'admin', 'subject': 'Nueva cuenta profesional pendiente: {center}', 'pre': 'Revisa la verificación.', 'blocks': [
   ('h', 'Nueva cuenta profesional'), ('p', '{pro_name} ({pro_email}) ha creado una cuenta de {pro_type}: {center}.'),
   ('button', ('Revisar verificaciones', 'admin_claims_url'))]},
 'admin_payment_review': {'to': 'admin', 'subject': 'Pago en revisión: {service} · {total}', 'pre': 'El importe no coincide.', 'blocks': [
   ('h', 'Pago en revisión'), ('p', 'El cobro de la reserva {ref} ({center}) no coincide con el importe esperado. Decide en Administración → Pagos.'),
   ('button', ('Abrir Pagos', 'admin_pay_url'))]},
 'admin_refund_failed': {'to': 'admin', 'subject': 'Devolución pendiente: {ref} · {total}', 'pre': 'Stripe no ha podido hacer la devolución.', 'blocks': [
   ('h', 'Devolución pendiente'), ('p', 'Hay una incidencia con el pago de la reserva {ref} ({center}, {total}). Las devoluciones las hace el centro desde su panel o su cuenta de Stripe; revisa el caso y márcalo en Administración → Pagos.'),
   ('note', '{error}'), ('button', ('Abrir Pagos', 'admin_pay_url'))]},
 'refund_issued': {'to': 'diver', 'subject': 'Te han devuelto {refund_amount} · {service}', 'pre': '{center} ha hecho la devolución.', 'blocks': [
   ('h', 'Devolución hecha'),
   ('p', 'Hola {first_name}, {center} te ha devuelto {refund_amount} de tu reserva del {date}. Lo verás en tu tarjeta en 5–10 días hábiles, según tu banco.'),
   ('note', '{refund_reason_text}'), ('details', None), ('button', ('Ver mi reserva', 'booking_url'))]},
 'center_refund_reminder': {'to': 'center', 'subject': 'Devolución pendiente: {ref} · {refund}', 'pre': 'Un cliente espera su devolución.', 'blocks': [
   ('h', 'Tienes una devolución pendiente'),
   ('p', '{diver_name} canceló su reserva del {date}. Según tu política de cancelación le corresponde una devolución de {refund}.'),
   ('p', 'Hazla desde la reserva en tu panel con el botón «Devolver». El dinero sale de tu cuenta de Stripe, igual que entró.'),
   ('details', None), ('button', ('Ver la reserva', 'panel_booking_url'))]},
 'center_dispute': {'to': 'center', 'subject': 'Disputa abierta en un pago: {ref}', 'pre': 'Respóndela desde tu panel de Stripe.', 'blocks': [
   ('h', 'El banco del cliente ha abierto una disputa'),
   ('p', 'El banco de {diver_name} ha abierto una disputa sobre el pago de la reserva {ref}. Las disputas las gestiona tu centro desde su panel de Stripe, donde puedes aportar pruebas (la reserva, el justificante, el registro de asistencia).'),
   ('note', '{dispute_reason}'), ('details', None)]},
 'admin_content_report': {'to': 'admin', 'subject': 'Nueva denuncia de contenido · {reason}', 'pre': '{target}', 'blocks': [
   ('h', 'Nueva denuncia de contenido'), ('p', 'Motivo: {reason}'), ('p', 'Contenido: {target}'), ('note', '{details}'),
   ('p', 'Remitente: {reporter}'), ('button', ('Revisar denuncias', 'admin_legal_url'))]},
 'report_received': {'to': 'any', 'subject': 'Hemos recibido tu denuncia · {ref}', 'pre': 'La revisaremos lo antes posible.', 'blocks': [
   ('h', 'Hemos recibido tu denuncia'),
   ('p', 'Hola {first_name}, gracias por avisarnos. Hemos registrado tu denuncia con la referencia {ref} (motivo: {reason}).'),
   ('p', 'La revisaremos con diligencia y de forma objetiva, y te escribiremos con la decisión que tomemos.')]},
 'report_resolved': {'to': 'any', 'subject': 'Resultado de tu denuncia · {ref}', 'pre': '{decision}', 'blocks': [
   ('h', 'Hemos revisado tu denuncia'), ('p', 'Hola {first_name}, hemos revisado la denuncia {ref}.'), ('note', '{decision}'), ('p', '{resolution}'),
   ('p', 'Si no estás de acuerdo con la decisión, puedes responder a este correo y la revisaremos de nuevo.')]},
 'verify_email': {'to': 'any', 'subject': 'Confirma tu email en WORLDIVES', 'pre': 'Un clic para confirmar tu dirección.', 'blocks': [
   ('h', 'Confirma tu email'),
   ('p', 'Hola {first_name}, confirma que esta dirección es tuya para recibir los avisos de tus reservas y poder recuperar tu cuenta.'),
   ('button', ('Confirmar mi email', 'verify_url')),
   ('note', 'El enlace caduca en 48 horas. Si no has creado una cuenta en WORLDIVES, ignora este correo.')]},
 'verify_email_change': {'to': 'any', 'subject': 'Confirma tu nuevo email en WORLDIVES', 'pre': 'Cambio de email de tu cuenta.', 'blocks': [
   ('h', 'Confirma tu nuevo email'),
   ('p', 'Hola {first_name}, has pedido usar {new_email} en tu cuenta de WORLDIVES. El cambio se aplica cuando confirmes desde este correo.'),
   ('button', ('Confirmar el cambio', 'verify_url')),
   ('note', 'Si no has pedido este cambio, ignora este correo: tu email no cambiará.')]},
 'booking_notice': {'to': 'diver', 'subject': 'Aviso de {provider}: {notice_subject}', 'pre': '{notice_subject}', 'blocks': [
   ('h', '{notice_subject}'),
   ('p', 'Hola {first_name}, {provider} te envía este aviso sobre tu reserva:'),
   ('note', '{notice_body}'),
   ('p', 'Este aviso no admite respuesta por WORLDIVES. Si necesitas contestar, contacta directamente con {provider}: teléfono {provider_phone} · email {provider_email}.'),
   ('button', ('Ver mi reserva', 'booking_url'))]},
 'medical_document_removed': {'to': 'any', 'subject': 'Hemos eliminado un certificado médico de tu cuenta', 'pre': 'Los datos de salud no se guardan en WORLDIVES.', 'blocks': [
   ('h', 'Certificado médico eliminado'),
   ('p', 'Hola {first_name}, para proteger tus datos de salud, WORLDIVES ya no guarda certificados médicos. Hemos eliminado el documento «{document}» y su archivo.'),
   ('p', 'Cuando un centro te lo pida, entrégaselo directamente a él.')]},
 'admin_error_alert': {'to': 'admin', 'subject': 'Alerta: {count} errores del servidor en pocos minutos', 'pre': 'Revisa el servidor.', 'blocks': [
   ('h', 'Errores repetidos en el servidor'), ('p', 'Se han producido {count} errores internos (500) en {site} en los últimos minutos. Los últimos:'),
   ('note', '{errors}'), ('p', 'Revisa los registros del servicio (journalctl -u worldives) y el estado en Administración → Sistema.')]},
 'test': {'to': 'any', 'subject': 'Correo de prueba de WORLDIVES DISCOVERY', 'pre': 'La configuración de correo funciona.', 'blocks': [
   ('h', '¡Funciona!'), ('p', 'Este es un correo de prueba. Si lo estás leyendo, el envío de correos de WORLDIVES está bien configurado.')]},
}
EMAIL_TEMPLATE_LABELS = {
 'welcome': 'Bienvenida (buceador)', 'welcome_pro': 'Bienvenida (centro / profesional)', 'password_reset': 'Restablecer contraseña',
 'password_changed': 'Aviso de contraseña cambiada', 'booking_request': 'Solicitud enviada', 'booking_confirmed': 'Reserva confirmada',
 'booking_manual': 'Reserva registrada por el centro', 'payment_required': 'Plaza aceptada: pago pendiente', 'payment_receipt': 'Recibo de pago',
 'payment_review': 'Pago en revisión', 'booking_rejected': 'Solicitud rechazada', 'booking_cancelled_center': 'Cancelada por el centro',
 'booking_cancelled_diver': 'Cancelada por el buceador', 'reminder': 'Recordatorio del día anterior', 'review_request': 'Petición de reseña',
 'promotion_received': 'Promoción recibida', 'experience_request': 'Solicitud de viaje enviada', 'experience_status': 'Respuesta a solicitud de viaje',
 'account_deleted': 'Cuenta eliminada', 'center_new_booking': 'Centro: nueva reserva', 'center_booking_paid': 'Centro: pago recibido',
 'center_booking_cancelled': 'Centro: cancelación del cliente', 'center_daily_agenda': 'Centro: agenda de mañana', 'center_promo_invite': 'Centro: invitación a promoción',
 'center_experience_request': 'Centro: nueva solicitud de viaje', 'center_verified': 'Centro: perfil verificado', 'admin_new_pro': 'Admin: nueva cuenta profesional',
 'refund_issued': 'Devolución hecha (buceador)', 'center_refund_reminder': 'Centro: devolución pendiente', 'center_dispute': 'Centro: disputa abierta',
 'admin_payment_review': 'Admin: pago en revisión', 'admin_refund_failed': 'Admin: devolución pendiente', 'admin_content_report': 'Admin: denuncia de contenido',
 'report_received': 'Denuncia recibida', 'report_resolved': 'Resultado de la denuncia', 'test': 'Correo de prueba',
 'booking_expired': 'Reserva caducada (buceador)', 'center_booking_expired': 'Centro: reserva caducada', 'center_payments_disabled': 'Centro: «Pago al reservar» sin cobros activos',
 'verify_email': 'Verificación de email', 'verify_email_change': 'Confirmación de cambio de email', 'booking_notice': 'Aviso del centro sobre una reserva',
 'medical_document_removed': 'Certificado médico eliminado', 'admin_error_alert': 'Admin: errores repetidos del servidor'}
EMAIL_AUDIENCE = {'diver': 'Buceador', 'pro': 'Profesional', 'center': 'Centro', 'admin': 'Administración', 'any': 'Cualquier usuario'}


def _esc(v): return html.escape(str(v if v is not None else ''), quote=True)


def booking_mail_ctx(db, bid, lang='es'):
    b = db.execute('''SELECT b.*, u.fullname, u.email, up.phone AS diver_phone, p.name AS point_name, s.title AS service_title, s.response_hours
                        FROM bookings b JOIN users u ON u.id=b.user_id LEFT JOIN user_profiles up ON up.user_id=u.id
                        LEFT JOIN dive_points p ON p.id=b.dive_point_id LEFT JOIN provider_services s ON s.id=b.service_id WHERE b.id=?''', (bid,)).fetchone()
    if not b: return None
    base = public_site_url()
    _svc, payee = booking_payee(db, b); payee = payee or {'type': 'center', 'id': b['center_id'], 'name': ''}
    prov_url = f"{base}/#/centro?id={payee['id']}" if payee['type'] == 'center' else f"{base}/#/profesional?id={payee['id']}"
    paid_net = round(float(b['amount_paid'] or 0) - float(b['refunded_total'] or 0), 2)
    po = db.execute("SELECT * FROM payment_orders WHERE booking_id=? ORDER BY CASE status WHEN 'paid' THEN 0 WHEN 'refunded' THEN 1 ELSE 2 END, id DESC LIMIT 1", (bid,)).fetchone()
    first = (b['contact_name'] if b['contact_name'] and is_guest_user(db, b['user_id']) else b['fullname'] or '').split(' ')[0]
    diver_email = b['email'] if mail_deliverable(b['email']) else (b['contact_email'] if mail_deliverable(b['contact_email']) else '')
    return {'booking_id': bid, 'ref': f'WOD-{bid:06d}', 'first_name': first or mail_t(lang, 'buceador'), 'diver_name': (b['contact_name'] or b['fullname'] or '') if is_guest_user(db, b['user_id']) else (b['fullname'] or ''), 'diver_email': diver_email,
            'diver_phone': b['diver_phone'] or b['contact_phone'] or '', 'center': payee.get('name') or '', 'center_id': b['center_id'], 'provider_user_id': b['provider_user_id'],
            'center_email': payee.get('email') or '', 'center_phone': payee.get('phone') or '', 'center_address': ', '.join(x for x in (payee.get('address'), payee.get('city')) if x),
            'deposit': mail_money(b['deposit_amount'], b['currency'], lang) if b['deposit_amount'] else '', 'amount_due': mail_money(b['amount_due'], b['currency'], lang) if b['amount_due'] else '',
            'paid': mail_money(paid_net, b['currency'], lang) if paid_net > 0 else '', 'refund': mail_money(b['refund_proposed'], b['currency'], lang) if b['refund_proposed'] else '',
            'refunded': mail_money(b['refunded_total'], b['currency'], lang) if b['refunded_total'] else '',
            'service': b['service_title'] or mail_t(lang, 'Inmersión'), 'point': b['point_name'] or '', 'date': mail_date(b['booking_date'], lang),
            'date_short': '/'.join(reversed(str(b['booking_date'] or '').split('-'))), 'time': b['booking_time'] or '', 'participants': int(b['participants'] or 1),
            'total': mail_money(b['price'], b['currency'], lang), 'price': float(b['price'] or 0), 'currency': b['currency'] or 'EUR', 'payment_status': b['payment_status'],
            'status': b['status'], 'equipment': b['equipment_items'] or '', 'notes': b['notes'] or '', 'booking_mode': b['booking_mode'], 'user_id': b['user_id'],
            'card': (f"{(po['card_brand'] or '').title()} ···· {po['card_last4']}" if po and po['card_last4'] else ''), 'pay_ref': f"PAY-{po['id']:05d}" if po else '',
            'policy': booking_policy(db, b, lang)['text'],
            'status_label': mail_t(lang, wbk.state_label(b['status'])), 'mode_label': mail_t(lang, wbk.mode_label(b['booking_mode'] or 'request', b['response_hours'])),
            'payment_deadline': mail_datetime(b['payment_deadline'], lang), 'response_deadline': mail_datetime(b['response_deadline'], lang),
            'reject_reason': b['reject_reason'] or '',
            'booking_url': f'{base}/#/reserva?id={bid}', 'pdf_url': f'{base}/api/bookings/{bid}/receipt.pdf', 'center_url': prov_url,
            'review_url': f"{base}/#/centro?id={b['center_id']}&resena=1" if b['center_id'] else prov_url, 'search_url': f'{base}/#/centros', 'panel_booking_url': f'{base}/#/admin?tab=bookings',
            'panel_planning_url': f'{base}/#/admin?tab=planning', 'admin_pay_url': f'{base}/#/admin?tab=adminpay'}


def render_email(db, template, lang, ctx):
    """Returns (subject, html, text) for a template in `lang`. Values from the context are inserted escaped."""
    tpl = EMAIL_TEMPLATES[template]; lang = lang if lang in MAIL_LANGS else 'es'
    t = lambda s, **kw: mail_t(lang, s, **kw)
    fmt = lambda s: mail_t(lang, s, **ctx)
    legal = legal_settings(db); base = public_site_url()
    rows_html = []; text = []
    P = 'margin:0 0 14px;font-size:15px;line-height:1.6;color:#2b3f48'

    def para(s, style=P):
        rows_html.append(f'<p style="{style}">{_esc(s)}</p>'); text.append(s); text.append('')

    def details_rows():
        items = [(t('Reserva'), ctx.get('ref')), (t('Actividad'), ctx.get('service')), (t('Centro'), ctx.get('center')), (t('Fecha'), ctx.get('date')),
                 (t('Hora'), ctx.get('time') or t('Por confirmar')), (t('Punto de buceo'), ctx.get('point') or t('A concretar con el centro')),
                 (t('Buceadores'), ctx.get('participants')), (t('Equipo de alquiler'), ctx.get('equipment')), (t('Total'), ctx.get('total'))]
        return [(k, v) for k, v in items if v not in (None, '', 0)]
    for kind, val in tpl['blocks']:
        if kind == 'h':
            s = fmt(val)
            rows_html.append(f'<h1 style="margin:0 0 16px;font-size:24px;line-height:1.25;color:#07364a;font-family:Georgia,\'Times New Roman\',serif;font-weight:500">{_esc(s)}</h1>')
            text += [s.upper(), '']
        elif kind == 'p':
            s = fmt(val)
            if s.strip(): para(s)
        elif kind == 'note':
            s = fmt(val)
            if s.strip():
                rows_html.append(f'<div style="margin:4px 0 18px;padding:14px 16px;border-radius:10px;background:#f1f7f8;border-left:4px solid #0b7a89;font-size:14px;line-height:1.55;color:#2b3f48">{_esc(s)}</div>')
                text += ['» ' + s, '']
        elif kind == 'list':
            lis = ''.join(f'<li style="margin:0 0 8px">{_esc(fmt(x))}</li>' for x in val)
            rows_html.append(f'<ul style="margin:0 0 18px;padding-left:20px;font-size:15px;line-height:1.55;color:#2b3f48">{lis}</ul>')
            text += ['- ' + fmt(x) for x in val] + ['']
        elif kind == 'code':
            s = fmt(val)
            rows_html.append(f'<div style="margin:4px 0 14px;padding:16px;border:2px dashed #0b7a89;border-radius:12px;text-align:center;font-size:18px;font-weight:700;color:#07364a">{_esc(s)}</div>')
            text += [s, '']
        elif kind == 'details':
            rws = details_rows()
            tr = ''.join(f'<tr><td style="padding:9px 12px;border-bottom:1px solid #e6eef0;color:#65747d;font-size:13px;width:38%;vertical-align:top">{_esc(k)}</td>'
                         f'<td style="padding:9px 12px;border-bottom:1px solid #e6eef0;font-size:14px;font-weight:600;color:#153142">{_esc(v)}</td></tr>' for k, v in rws)
            rows_html.append(f'<table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin:4px 0 18px;border:1px solid #e6eef0;border-radius:10px;border-collapse:separate;overflow:hidden">{tr}</table>')
            text += [f'{k}: {v}' for k, v in rws] + ['']
        elif kind == 'payment':
            ps = ctx.get('payment_status'); s = ''
            if ctx.get('price', 0) <= 0: s = t('Actividad sin coste.')
            elif ps == 'paid':
                s = t('Pagado: {total}', total=ctx.get('total')) + (f" · {ctx['card']}" if ctx.get('card') else '') + (f" · {t('Ref. del pago')} {ctx['pay_ref']}" if ctx.get('pay_ref') else '')
            elif ps == 'at_center': s = t('Pago en el centro: {total}, el día de la actividad.', total=ctx.get('total'))
            elif ps in ('required', 'pending'): s = t('Pago pendiente: {total}.', total=ctx.get('total'))
            elif ps == 'deposit_paid':
                s = t('Señal pagada: {paid}. Resto a pagar en el centro: {due}.', paid=ctx.get('paid') or ctx.get('deposit'), due=ctx.get('amount_due')) + (f" · {ctx['card']}" if ctx.get('card') else '')
            elif ps == 'refunded': s = t('Importe devuelto: {total}.', total=ctx.get('refunded') or ctx.get('total'))
            elif ps == 'partially_refunded': s = t('Pagado: {paid} · devuelto: {refunded}.', paid=ctx.get('total'), refunded=ctx.get('refunded'))
            if ps in ('required', 'pending') and ctx.get('deposit'): s = t('Señal a pagar online: {deposit}. El resto, {due}, se paga en el centro.', deposit=ctx['deposit'], due=ctx.get('amount_due'))
            if s: para(s, 'margin:0 0 16px;font-size:14px;line-height:1.5;color:#1f6b52;font-weight:600')
        elif kind == 'policy':
            if ctx.get('policy'): para(t('Política de cancelación del centro: {policy}', policy=ctx['policy']), 'margin:0 0 14px;font-size:13px;line-height:1.5;color:#65747d')
        elif kind == 'bring':
            items = [t('Llega 15–20 minutos antes de la hora.'), t('Lleva tu titulación y el seguro de buceo.'), t('Documento de identidad o pasaporte.')]
            if ctx.get('center_address'): items.append(t('Dirección del centro: {address}', address=ctx['center_address']))
            if ctx.get('center_phone'): items.append(t('Teléfono del centro: {phone}', phone=ctx['center_phone']))
            lis = ''.join(f'<li style="margin:0 0 6px">{_esc(x)}</li>' for x in items)
            rows_html.append(f'<p style="margin:6px 0 8px;font-size:12px;font-weight:700;color:#07364a;text-transform:uppercase;letter-spacing:.08em">{_esc(t("Antes de bucear"))}</p>'
                             f'<ul style="margin:0 0 18px;padding-left:20px;font-size:14px;line-height:1.5;color:#2b3f48">{lis}</ul>')
            text += [t('Antes de bucear').upper()] + ['- ' + x for x in items] + ['']
        elif kind == 'diver':
            rws = [(t('Cliente'), ctx.get('diver_name')), (t('Email'), ctx.get('diver_email')), (t('Teléfono'), ctx.get('diver_phone')), (t('Notas'), ctx.get('notes'))]
            rws = [(k, v) for k, v in rws if v]
            tr = ''.join(f'<tr><td style="padding:6px 0;color:#65747d;font-size:13px;width:38%">{_esc(k)}</td><td style="padding:6px 0;font-size:14px;color:#153142">{_esc(v)}</td></tr>' for k, v in rws)
            rows_html.append(f'<table role="presentation" width="100%" style="margin:0 0 16px">{tr}</table>'); text += [f'{k}: {v}' for k, v in rws] + ['']
        elif kind == 'agenda':
            for sl in ctx.get('agenda', []):
                people = ''.join(f'<li style="margin:0 0 4px">{_esc(p)}</li>' for p in sl['people']) or f'<li>{_esc(t("Sin reservas todavía"))}</li>'
                rows_html.append(f'<div style="margin:0 0 14px;padding:12px 14px;border:1px solid #e6eef0;border-radius:10px"><div style="font-size:15px;font-weight:700;color:#07364a">{_esc(sl["time"])} · {_esc(sl["title"])}</div>'
                                 f'<div style="font-size:13px;color:#65747d;margin:2px 0 8px">{_esc(t("Buceadores") + ": " + str(sl["taken"]) if sl.get("loose") else t("{taken} de {total} plazas ocupadas", taken=sl["taken"], total=sl["total"]))}{(" · " + _esc(sl["points"])) if sl.get("points") else ""}</div>'
                                 f'<ul style="margin:0;padding-left:18px;font-size:14px;color:#2b3f48">{people}</ul></div>')
                text += [f"{sl['time']} · {sl['title']} ({sl['taken']}/{sl['total']})"] + ['  - ' + p for p in sl['people']] + ['']
        elif kind == 'button':
            label, key = val; url = ctx.get(key) or base; s = fmt(label)
            rows_html.append(f'<table role="presentation" cellpadding="0" cellspacing="0" style="margin:8px 0 22px"><tr><td style="border-radius:999px;background:#07364a">'
                             f'<a href="{_esc(url)}" style="display:inline-block;padding:13px 24px;font-size:15px;font-weight:700;color:#ffffff;text-decoration:none;border-radius:999px">{_esc(s)}</a></td></tr></table>')
            text += [f'{s}: {url}', '']
    subject = fmt(tpl['subject']); pre = fmt(tpl.get('pre', ''))
    who = {'diver': 'Recibes este correo porque tienes una cuenta o una reserva en WORLDIVES DISCOVERY.',
           'center': 'Recibes este correo porque gestionas un centro o un perfil profesional en WORLDIVES DISCOVERY.',
           'pro': 'Recibes este correo porque has creado una cuenta profesional en WORLDIVES DISCOVERY.',
           'admin': 'Aviso interno para la administración de WORLDIVES DISCOVERY.', 'any': 'Correo de servicio de WORLDIVES DISCOVERY.'}[tpl.get('to', 'any')]
    owner = legal.get('owner_name') or 'WORLDIVES DISCOVERY'
    foot_addr = ' · '.join(x for x in (owner, (f"NIF {legal['nif']}" if legal.get('nif') else ''), legal.get('address'), legal.get('email')) if x)
    html_lang = HTML_LANG.get(lang, lang)
    html_doc = f'''<!doctype html><html lang="{_esc(html_lang)}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light"><title>{_esc(subject)}</title></head>
<body style="margin:0;padding:0;background:#f2efe8;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;-webkit-text-size-adjust:100%">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;color:transparent">{_esc(pre)}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f2efe8"><tr><td align="center" style="padding:24px 12px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 6px 24px rgba(7,54,74,.08)">
<tr><td style="background:#07364a;padding:20px 28px"><table role="presentation" cellpadding="0" cellspacing="0"><tr>
<td style="padding-right:12px"><img src="{_esc(base)}/assets/images/wod-icon-512.png" width="40" height="40" alt="" style="display:block;border-radius:10px;background:#ffffff"></td>
<td><a href="{_esc(base)}" style="color:#ffffff;text-decoration:none;font-size:17px;font-weight:800;letter-spacing:.06em">WORLDIVES DISCOVERY</a><div style="height:3px;width:42px;background:#12a5b5;margin-top:8px;border-radius:3px"></div></td></tr></table></td></tr>
<tr><td style="padding:30px 28px 8px">{''.join(rows_html)}</td></tr>
<tr><td style="padding:18px 28px 26px;border-top:1px solid #eef2f3;font-size:12px;line-height:1.55;color:#7d8d94">{_esc(t(who))}<br>{_esc(foot_addr)}<br>
<a href="{_esc(base)}/#/legal/privacidad" style="color:#0b7a89">{_esc(t('Política de privacidad'))}</a> · <a href="{_esc(base)}/#/legal/reservas" style="color:#0b7a89">{_esc(t('Condiciones de reserva'))}</a> · <a href="{_esc(base)}/#/legal/aviso-legal" style="color:#0b7a89">{_esc(t('Aviso legal'))}</a></td></tr>
</table></td></tr></table></body></html>'''
    text_doc = '\n'.join(text).strip() + '\n\n--\n' + t(who) + '\n' + foot_addr + '\n' + f'{base}/#/legal/privacidad\n'
    return subject, html_doc, text_doc


def queue_email(db, template, to_email, to_name, ctx, lang='es', related=None):
    """Renders and stores an email in the outbox, inside the caller's transaction. Never raises."""
    try:
        subject, html_doc, text_doc = render_email(db, template, lang, ctx)
        status = 'queued' if mail_deliverable(to_email) else 'skipped'
        rel = related or (None, None)
        db.execute('INSERT INTO email_outbox(template,lang,to_email,to_name,subject,html,text,status,related_type,related_id,attempts,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,0,?)',
                   (template, lang, (to_email or '').strip().lower(), to_name or '', subject, html_doc, text_doc, status, rel[0], rel[1], now()))
    except Exception as exc:
        sys.stderr.write(f'[correo] no se pudo preparar «{template}»: {exc}\n')


def user_mail_ctx(db, user_id):
    u = db.execute('SELECT id,fullname,email,role,center_id FROM users WHERE id=?', (user_id,)).fetchone()
    if not u: return None, 'es'
    lang = user_lang(db, u['id']); base = public_site_url()
    return {'first_name': (u['fullname'] or '').split(' ')[0], 'name': u['fullname'] or '', 'email': u['email'] or '',
            'account_url': f'{base}/#/cuenta', 'panel_url': f'{base}/#/admin', 'area_url': f'{base}/#/area', 'forgot_url': f'{base}/#/recuperar',
            'promo_url': f'{base}/#/recompensas', 'search_url': f'{base}/#/centros', 'panel_qr_url': f'{base}/#/admin?tab=qr',
            'panel_exp_url': f'{base}/#/admin?tab=experiences', 'admin_claims_url': f'{base}/#/admin?tab=claims', 'admin_pay_url': f'{base}/#/admin?tab=adminpay',
            'admin_legal_url': f'{base}/#/admin?tab=legal', 'panel_planning_url': f'{base}/#/admin?tab=planning'}, lang


def notify_user(db, user_id, template, extra=None, related=None):
    ctx, lang = user_mail_ctx(db, user_id)
    if not ctx: return
    ctx.update(extra or {})
    queue_email(db, template, ctx['email'], ctx['name'], ctx, lang, related)


def center_recipients(db, center_id):
    """Who receives a centre's emails: its manager accounts and, if different, the centre's public email."""
    out = {}
    for r in db.execute("SELECT id,fullname,email FROM users WHERE center_id=? AND role='center'", (center_id,)).fetchall():
        if mail_deliverable(r['email']): out[r['email'].lower()] = (r['fullname'], user_lang(db, r['id']))
    c = db.execute('SELECT name,email FROM centers WHERE id=?', (center_id,)).fetchone()
    if c and mail_deliverable(c['email']) and c['email'].lower() not in out: out[c['email'].lower()] = (c['name'], 'es')
    return [(e, n, l) for e, (n, l) in out.items()]


def provider_recipients(db, center_id=None, user_id=None):
    """The provider of a booking: the centre's recipients, or the freelance professional without a centre."""
    if center_id: return center_recipients(db, center_id)
    u = db.execute('SELECT id,fullname,email FROM users WHERE id=?', (user_id,)).fetchone() if user_id else None
    return [(u['email'], u['fullname'], user_lang(db, u['id']))] if u and mail_deliverable(u['email']) else []


def admin_recipients(db):
    legal = legal_settings(db); out = []
    if mail_deliverable(legal.get('email')): out.append((legal['email'], legal.get('owner_name') or 'WORLDIVES', 'es'))
    for r in db.execute("SELECT fullname,email FROM users WHERE role='admin' ORDER BY id LIMIT 3").fetchall():
        if mail_deliverable(r['email']) and all(r['email'].lower() != o[0].lower() for o in out): out.append((r['email'], r['fullname'], 'es'))
    return out


def notify_admins(db, template, ctx, related=None):
    base_ctx, _ = user_mail_ctx(db, 0) if False else ({}, 'es')
    base = public_site_url()
    full = {'admin_claims_url': f'{base}/#/admin?tab=claims', 'admin_pay_url': f'{base}/#/admin?tab=adminpay', 'admin_legal_url': f'{base}/#/admin?tab=legal', **(ctx or {})}
    for email, name, lang in admin_recipients(db):
        queue_email(db, template, email, name, full, lang, related)


def refund_texts(lang, outcome, amount_text):
    """outcome: 'none_paid' | 'refunded' | 'refund_pending' | 'no_refund'."""
    t = lambda s, **kw: mail_t(lang, s, **kw)
    if outcome == 'refunded': return {'refund_note': t('Te devolvemos {amount} a la misma tarjeta. Lo verás en tu cuenta en 5–10 días hábiles, según tu banco.', amount=amount_text), 'refund_short': t('Te devolvemos {amount}.', amount=amount_text)}
    if outcome == 'refund_pending': return {'refund_note': t('Vamos a devolverte {amount} a la misma tarjeta. Te avisaremos cuando la devolución esté hecha.', amount=amount_text), 'refund_short': t('Te devolvemos {amount}.', amount=amount_text)}
    if outcome == 'proposed': return {'refund_note': t('Según la política de cancelación del centro te corresponde una devolución de {amount}. Se la hemos pedido al centro, que la hace desde su cuenta; te avisaremos por email cuando esté hecha.', amount=amount_text), 'refund_short': t('Devolución de {amount} solicitada al centro.', amount=amount_text)}
    if outcome == 'no_refund': return {'refund_note': t('Según la política de cancelación del centro, esta cancelación no tiene reembolso.'), 'refund_short': t('Cancelación sin reembolso.')}
    return {'refund_note': t('No se te había cobrado nada.'), 'refund_short': t('No se te había cobrado nada.')}


def notify_booking(db, bid, event, extra=None):
    """Emails for a booking event to the diver and, when it matters, to the centre and the administrators."""
    try:
        b = db.execute('SELECT user_id,center_id,provider_user_id FROM bookings WHERE id=?', (bid,)).fetchone()
        if not b: return
        lang_d = user_lang(db, b['user_id'])
        ctx = booking_mail_ctx(db, bid, lang_d)
        if not ctx: return
        extra = extra or {}; ctx.update(extra)
        rel = ('booking', bid)

        def to_diver(tpl, more=None):
            c = dict(ctx); c.update(more or {})
            if c.get('diver_email'): queue_email(db, tpl, c['diver_email'], c['diver_name'], c, lang_d, rel)

        def to_center(tpl, more=None):
            for email, name, lang in provider_recipients(db, b['center_id'], b['provider_user_id']):
                c = booking_mail_ctx(db, bid, lang) or dict(ctx); c.update(extra); c.update(more or {})
                for k in ('action_title', 'action_short', 'action_button', 'center_refund_note', 'expired_text'):
                    if c.get(k): c[k] = mail_t(lang, c[k], **{kk: vv for kk, vv in c.items() if isinstance(vv, (str, int, float))})
                queue_email(db, tpl, email, name, c, lang, rel)
        if event == 'created':
            if ctx['status'] == 'confirmed':
                to_diver('booking_confirmed')
                to_center('center_new_booking', {'action_title': 'Nueva reserva confirmada', 'action_short': 'Reserva confirmada', 'action_button': 'Ver la reserva'})
            else:
                pay_note = ('No se cobra nada hasta que el centro acepte. Si acepta, pagarás directamente en el centro el día de la actividad.' if ctx['payment_status'] == 'at_center' else
                            'No se cobra nada hasta que el centro acepte. Si acepta, te avisaremos para pagar online antes del plazo que te indiquemos.' if ctx['payment_status'] == 'required' else
                            'No se cobra nada hasta que el centro acepte.')
                to_diver('booking_request', {'pay_note': mail_t(lang_d, pay_note)})
                to_center('center_new_booking', {'action_title': 'Nueva solicitud: acéptala o recházala', 'action_short': 'Responde antes de {response_deadline}', 'action_button': 'Aceptar o rechazar'})
        elif event == 'accepted_payment':
            to_diver('payment_required')
        elif event == 'expired_no_response':
            to_diver('booking_expired', {'expired_text': mail_t(lang_d, '{center} no ha respondido a tu solicitud dentro del plazo, así que la hemos cerrado. No se te ha cobrado nada.', center=ctx['center'])})
            to_center('center_booking_expired', {'expired_text': 'La solicitud de {diver_name} ha caducado porque no se respondió antes del plazo. El buceador ya está avisado.'})
        elif event == 'expired_not_paid':
            to_diver('booking_expired', {'expired_text': mail_t(lang_d, 'No hemos recibido el pago dentro del plazo, así que la reserva se ha cancelado y las plazas se han liberado. No se te ha cobrado nada.')})
            to_center('center_booking_expired', {'expired_text': 'La reserva aceptada de {diver_name} se ha cancelado porque no se pagó dentro del plazo. Las plazas vuelven a estar libres.'})
        elif event == 'manual':
            to_diver('booking_manual')
        elif event == 'confirmed':
            if ctx['payment_status'] == 'required' and ctx['price'] > 0: to_diver('payment_required')
            else: to_diver('booking_confirmed')
        elif event == 'paid':
            if extra.get('was_confirmed'):
                to_diver('payment_receipt'); to_center('center_booking_paid')
            else:
                to_diver('booking_confirmed')
                to_center('center_new_booking', {'action_title': 'Nueva reserva pagada', 'action_short': 'Pagada online y confirmada', 'action_button': 'Ver la reserva'})
        elif event == 'payment_review':
            to_diver('payment_review')
            notify_admins(db, 'admin_payment_review', ctx, rel)
        elif event == 'rejected':
            reason = extra.get('reason') or ctx.get('reject_reason') or ''
            to_diver('booking_rejected', dict(refund_texts(lang_d, extra.get('refund', 'none_paid'), ctx['total']),
                                              reject_reason_text=mail_t(lang_d, 'Motivo indicado por el centro: {reason}', reason=reason) if reason else ''))
        elif event == 'cancelled_center':
            to_diver('booking_cancelled_center', refund_texts(lang_d, extra.get('refund', 'none_paid'), ctx['total']))
        elif event == 'cancelled_diver':
            outcome = extra.get('refund', 'none_paid')
            to_diver('booking_cancelled_diver', refund_texts(lang_d, outcome, ctx.get('refund') or ctx['total']))
            note = {'proposed': 'Según tu política de cancelación corresponde devolver {refund} al cliente. Hazlo desde la reserva en tu panel con el botón «Devolver».',
                    'refunded': 'El importe se ha devuelto al cliente según tu política de cancelación.',
                    'refund_pending': 'La devolución al cliente está en curso.',
                    'no_refund': 'Cancelación fuera de plazo: según tu política de cancelación, no hay reembolso.'}.get(outcome, 'El cliente no había pagado online.')
            to_center('center_booking_cancelled', {'center_refund_note': note})
        elif event == 'refund_issued':
            amount_text = mail_money(extra.get('amount'), ctx['currency'], lang_d)
            to_diver('refund_issued', {'refund_amount': amount_text, 'refund_reason_text': mail_t(lang_d, 'Nota del centro: {note}', note=extra['note']) if extra.get('note') else ''})
        elif event == 'refund_reminder':
            to_center('center_refund_reminder')
        elif event == 'dispute':
            to_center('center_dispute', {'dispute_reason': extra.get('reason') or ''})
            notify_admins(db, 'admin_refund_failed', dict(ctx, error=mail_t('es', 'Disputa abierta por el banco del cliente: {reason}', reason=extra.get('reason') or '')), rel)
        elif event == 'refund_failed':
            to_center('center_refund_reminder')
            notify_admins(db, 'admin_refund_failed', dict(ctx, error=extra.get('error', '')), rel)
        elif event == 'reminder': to_diver('reminder')
        elif event == 'review': to_diver('review_request')
    except Exception as exc:
        sys.stderr.write(f'[correo] aviso de reserva {bid}/{event}: {exc}\n')


def _smtp_open(cfg):
    if cfg['security'] == 'ssl':
        s = _smtplib.SMTP_SSL(cfg['host'], cfg['port'], timeout=20)
    else:
        s = _smtplib.SMTP(cfg['host'], cfg['port'], timeout=20)
        if cfg['security'] == 'starttls': s.starttls()
    if cfg['user']: s.login(cfg['user'], cfg['password'])
    return s


def _build_message(cfg, row):
    msg = _EmailMessage()
    msg['Subject'] = row['subject']; msg['From'] = _formataddr((cfg['from_name'], cfg['from']))
    msg['To'] = _formataddr((row['to_name'] or '', row['to_email'])); msg['Message-ID'] = _make_msgid(domain=cfg['from'].split('@')[-1])
    if cfg['reply_to']: msg['Reply-To'] = cfg['reply_to']
    msg['Auto-Submitted'] = 'auto-generated'
    msg.set_content(row['text'] or '')
    msg.add_alternative(row['html'] or '', subtype='html')
    return msg


def send_one_email(cfg, row, conn=None):
    """Sends one email. With `conn` the open SMTP connection is reused (batch sending)."""
    msg = _build_message(cfg, row)
    if conn is not None:
        conn.send_message(msg); return
    s = _smtp_open(cfg)
    try: s.send_message(msg)
    finally:
        try: s.quit()
        except Exception: pass


def deliver_outbox_once(limit=150):
    """Sends a batch of queued emails over one SMTP connection. Returns how many were sent."""
    cfg = smtp_config()
    if not cfg['enabled']: return 0
    db = None; sent = 0; conn = None
    try:
        db = connect()
        cutoff = (datetime.now(timezone.utc) - _timedelta(hours=72)).isoformat(timespec='seconds')
        db.execute("UPDATE email_outbox SET status='expired' WHERE status='queued' AND created_at<?", (cutoff,))
        db.execute("UPDATE email_outbox SET status='queued' WHERE status='sending' AND created_at<?", ((datetime.now(timezone.utc) - _timedelta(minutes=15)).isoformat(timespec='seconds'),))
        db.commit()
        rows = db.execute("SELECT * FROM email_outbox WHERE status='queued' AND (next_try_at IS NULL OR next_try_at<=?) ORDER BY id LIMIT ?", (now(), limit)).fetchall()
        for r in rows:
            if db.execute("UPDATE email_outbox SET status='sending' WHERE id=? AND status='queued'", (r['id'],)).rowcount != 1: db.commit(); continue
            db.commit()
            try:
                if conn is None: conn = _smtp_open(cfg)
                send_one_email(cfg, r, conn)
                db.execute("UPDATE email_outbox SET status='sent',sent_at=?,attempts=attempts+1,last_error=NULL WHERE id=?", (now(), r['id'])); sent += 1
            except Exception as exc:
                try:
                    if conn is not None: conn.close()
                except Exception: pass
                conn = None
                att = int(r['attempts'] or 0) + 1
                nxt = (datetime.now(timezone.utc) + _timedelta(minutes=min(60, 2 ** att))).isoformat(timespec='seconds')
                db.execute("UPDATE email_outbox SET status=?,attempts=?,last_error=?,next_try_at=? WHERE id=?", ('failed' if att >= 6 else 'queued', att, str(exc)[:300], nxt, r['id']))
                sys.stderr.write(f'[correo] envío {r["id"]} fallido: {exc}\n')
            db.commit()
    except Exception as exc:
        sys.stderr.write(f'[correo] cola: {exc}\n')
    finally:
        if conn is not None:
            try: conn.quit()
            except Exception: pass
        if db: db.close()
    return sent


def queue_center_agendas(db, day):
    """Tomorrow's departures for each centre, with its divers (sent once per centre and day).
    Bookings without a departure (entered by date only) are listed too."""
    rows = db.execute('''SELECT s.id AS slot_id, s.slot_time, s.spots_total, s.spots_available, ps.title, ps.center_id
                           FROM service_slots s JOIN provider_services ps ON ps.id=s.service_id
                          WHERE s.slot_date=? AND ps.center_id IS NOT NULL AND s.status IN ('open','full') ORDER BY ps.center_id, s.slot_time''', (day,)).fetchall()
    loose = db.execute('''SELECT b.center_id, b.booking_time, b.participants, b.equipment_items, u.fullname, COALESCE(ps.title,'Reserva') AS title
                            FROM bookings b JOIN users u ON u.id=b.user_id LEFT JOIN provider_services ps ON ps.id=b.service_id
                           WHERE b.booking_date=? AND b.slot_id IS NULL AND b.status IN ('confirmed','pending') ORDER BY b.center_id, b.booking_time''', (day,)).fetchall()
    by_center = {}
    for r in rows: by_center.setdefault(r['center_id'], {'slots': [], 'loose': []})['slots'].append(r)
    for r in loose: by_center.setdefault(r['center_id'], {'slots': [], 'loose': []})['loose'].append(r)
    for cid, grp in by_center.items():
        if db.execute('SELECT 1 FROM email_digest_log WHERE center_id=? AND digest_date=?', (cid, day)).fetchone(): continue
        agenda = []; divers = 0
        for s in grp['slots']:
            people = []
            for b in db.execute('''SELECT u.fullname, b.participants, b.equipment_items FROM bookings b JOIN users u ON u.id=b.user_id
                                    WHERE b.slot_id=? AND b.status IN ('confirmed','pending') ORDER BY b.id''', (s['slot_id'],)).fetchall():
                divers += int(b['participants'] or 1)
                people.append(f"{b['fullname']} · {int(b['participants'] or 1)} pax" + (f" · {b['equipment_items']}" if b['equipment_items'] else ''))
            pts = ', '.join(r['name'] for r in db.execute('SELECT p.name FROM service_slot_points sp JOIN dive_points p ON p.id=sp.dive_point_id WHERE sp.slot_id=?', (s['slot_id'],)).fetchall())
            agenda.append({'time': s['slot_time'], 'title': s['title'], 'taken': int(s['spots_total']) - int(s['spots_available']), 'total': int(s['spots_total']), 'people': people, 'points': pts})
        loose_by = {}
        for b in grp['loose']:
            divers += int(b['participants'] or 1)
            loose_by.setdefault((b['booking_time'] or '—', b['title']), []).append(f"{b['fullname']} · {int(b['participants'] or 1)} pax" + (f" · {b['equipment_items']}" if b['equipment_items'] else ''))
        for (tm, title), people in sorted(loose_by.items()):
            n = sum(int(x.split(' · ')[1].split(' ')[0]) for x in people)
            agenda.append({'time': tm, 'title': title, 'taken': n, 'total': n, 'people': people, 'points': '', 'loose': True})
        agenda.sort(key=lambda a: str(a['time']))
        if not any(a['people'] for a in agenda):
            db.execute('INSERT OR IGNORE INTO email_digest_log(center_id,digest_date,sent_at) VALUES(?,?,?)', (cid, day, now())); continue
        base = public_site_url()
        for email, name, lang in center_recipients(db, cid):
            queue_email(db, 'center_daily_agenda', email, name, {'agenda': agenda, 'date': mail_date(day, lang), 'date_short': '/'.join(reversed(day.split('-'))),
                        'slots_count': len(agenda), 'divers_count': divers, 'panel_planning_url': f'{base}/#/admin?tab=planning'}, lang, ('center', cid))
        db.execute('INSERT OR IGNORE INTO email_digest_log(center_id,digest_date,sent_at) VALUES(?,?,?)', (cid, day, now()))


def run_email_jobs(db, at=None):
    """Hourly jobs: reminders (day before), review requests (after the dive), centres' agenda (from 18:00) and cleanup."""
    at = at or datetime.now(); today = at.date(); tomorrow = (today + _timedelta(days=1)).isoformat(); yesterday = (today - _timedelta(days=1)).isoformat()
    if at.hour >= 9:
        for r in db.execute("SELECT id FROM bookings WHERE status='confirmed' AND booking_date=? AND reminder_sent_at IS NULL", (tomorrow,)).fetchall():
            if db.execute('UPDATE bookings SET reminder_sent_at=? WHERE id=? AND reminder_sent_at IS NULL', (now(), r['id'])).rowcount == 1: notify_booking(db, r['id'], 'reminder')
    for r in db.execute("SELECT id FROM bookings WHERE status IN ('confirmed','completed') AND booking_date BETWEEN ? AND ? AND review_asked_at IS NULL",
                        ((today - _timedelta(days=7)).isoformat(), yesterday)).fetchall():
        if db.execute('UPDATE bookings SET review_asked_at=? WHERE id=? AND review_asked_at IS NULL', (now(), r['id'])).rowcount == 1: notify_booking(db, r['id'], 'review')
    if at.hour >= 18: queue_center_agendas(db, tomorrow)
    db.execute('DELETE FROM email_outbox WHERE created_at<?', ((datetime.now(timezone.utc) - _timedelta(days=120)).isoformat(timespec='seconds'),))
    db.execute('DELETE FROM password_resets WHERE expires_at<?', ((datetime.now(timezone.utc) - _timedelta(days=2)).isoformat(timespec='seconds'),))
    db.commit()


def email_scheduler():
    """Background loop: deliver the outbox continuously (batches over one SMTP connection) and run the hourly jobs."""
    last_jobs = 0.0
    while True:
        # A full batch means more are waiting: keep sending; otherwise check again in a few seconds.
        sent = deliver_outbox_once()
        time.sleep(0.2 if sent >= 150 else 5)
        if time.time() - last_jobs < 3600: continue
        last_jobs = time.time(); db = None
        try:
            db = connect(); run_email_jobs(db)
        except Exception as exc:
            sys.stderr.write(f'[correo] tareas programadas: {exc}\n')
        finally:
            if db: db.close()


def sample_email_ctx(template, lang='es'):
    """Realistic example data for the admin preview of every template."""
    base = public_site_url(); t = lambda s: mail_t(lang, s)
    c = {'booking_id': 123, 'ref': 'WOD-000123', 'first_name': 'Laura', 'name': 'Laura Martín', 'diver_name': 'Laura Martín', 'diver_email': 'laura@ejemplo.com', 'diver_phone': '+34 600 000 000',
         'center': 'Centro de buceo de ejemplo', 'center_email': 'info@centro.example', 'center_phone': '+34 965 000 000', 'center_address': 'Puerto deportivo, 03730 Xàbia',
         'service': 'Buceo doble', 'point': 'Cabo San Martín', 'date': mail_date('2026-10-17', lang), 'date_short': '17/10/2026', 'time': '09:00', 'participants': 2,
         'total': mail_money(150, 'EUR', lang), 'price': 150.0, 'payment_status': 'paid', 'status': 'confirmed', 'equipment': 'Traje de neopreno ×1', 'notes': 'Primera inmersión del año',
         'card': 'Visa ···· 4242', 'pay_ref': 'PAY-00042', 'policy': policy_text(48, 50, lang), 'refund': mail_money(75, 'EUR', lang), 'refund_amount': mail_money(75, 'EUR', lang),
         'refund_reason_text': mail_t(lang, 'Nota del centro: {note}', note='Cancelación por mal tiempo'), 'dispute_reason': 'fraudulent', 'deposit': '', 'amount_due': '', 'paid': '', 'refunded': '',
         'booking_url': f'{base}/#/reserva?id=123', 'pdf_url': f'{base}/api/bookings/123/receipt.pdf', 'center_url': f'{base}/#/centros', 'review_url': f'{base}/#/centros',
         'search_url': f'{base}/#/centros', 'panel_booking_url': f'{base}/#/admin?tab=bookings', 'panel_planning_url': f'{base}/#/admin?tab=planning',
         'account_url': f'{base}/#/cuenta', 'panel_url': f'{base}/#/admin', 'reset_url': f'{base}/#/restablecer?token=ejemplo', 'forgot_url': f'{base}/#/recuperar',
         'when': '17/10/2026 18:30', 'pay_note': t('Pagarás directamente en el centro el día de la actividad.'),
         'promo_title': 'Curso Open Water + 1 año de equipo', 'promo_value': 'Equipo completo gratis durante 12 meses', 'valid_until': '30/06/2027',
         'promo_url': f'{base}/#/recompensas', 'experience': 'Semana en las Islas Medas', 'area_url': f'{base}/#/area', 'status_title': t('Solicitud confirmada'),
         'status_text': mail_t(lang, 'tu plaza en «{experience}» está confirmada. El organizador te contactará con los detalles.', experience='Semana en las Islas Medas'),
         'action_title': t('Nueva solicitud: confírmala'), 'action_short': t('Pendiente de que la confirmes'), 'action_button': t('Confirmar o rechazar'),
         'issuer': 'Centro de buceo de ejemplo', 'panel_qr_url': f'{base}/#/admin?tab=qr', 'panel_exp_url': f'{base}/#/admin?tab=experiences',
         'pro_name': 'Pedro Ruiz', 'pro_email': 'pedro@centro.example', 'pro_type': t('centro de buceo'), 'admin_claims_url': f'{base}/#/admin?tab=claims',
         'admin_pay_url': f'{base}/#/admin?tab=adminpay', 'admin_legal_url': f'{base}/#/admin?tab=legal', 'error': 'charge_already_refunded',
         'center_refund_note': t('El importe se ha devuelto automáticamente al cliente según tu política de cancelación.'),
         'reason': t('Información falsa o engañosa'), 'target': f'{base}/#/punto?id=40', 'details': 'La profundidad indicada no es correcta.', 'reporter': 'Laura Martín · laura@ejemplo.com',
         'slots_count': 2, 'divers_count': 7, 'payment_deadline': mail_datetime('2026-10-15T18:30', lang), 'response_deadline': mail_datetime('2026-10-12T18:30', lang),
         'mode_label': t('Bajo petición · el centro responde en 24 h'), 'status_label': t('Confirmada'), 'services': 'Bautizo de buceo, Buceo doble',
         'expired_text': mail_t(lang, 'No hemos recibido el pago dentro del plazo, así que la reserva se ha cancelado y las plazas se han liberado. No se te ha cobrado nada.'),
         'reject_reason_text': mail_t(lang, 'Motivo indicado por el centro: {reason}', reason='Mal estado del mar previsto'),
         'agenda': [{'time': '09:00', 'title': 'Buceo doble', 'taken': 5, 'total': 12, 'points': 'Cabo San Martín, Isla del Portitxol', 'people': ['Laura Martín · 2 pax · Traje de neopreno ×1', 'Marc Soler · 3 pax']},
                    {'time': '15:30', 'title': 'Bautizo de buceo', 'taken': 2, 'total': 6, 'points': 'Cala Blanca', 'people': ['Elena Vidal · 2 pax · Equipo completo ×2']}]}
    c.update(refund_texts(lang, 'refunded', c['total']))
    return c



# ---------------------------------------------------------------------------
# Legal documents, cancellations with refunds, password reset, privacy rights and content reports (v50.30)
# ---------------------------------------------------------------------------
LEGAL_VERSION = '2026-10-11'


def legal_doc_version(db, slug):
    """Current version of a legal document (editable documents with history arrive in Fase 5)."""
    try:
        row = db.execute('SELECT version FROM legal_doc_versions WHERE slug=? AND published_at<=? ORDER BY published_at DESC, id DESC LIMIT 1', (slug, now())).fetchone()
        if row: return row['version']
    except sqlite3.OperationalError:
        pass
    return LEGAL_VERSION
LEGAL_DOCS = {
    'aviso-legal': 'Aviso legal', 'terminos': 'Condiciones de uso', 'reservas': 'Condiciones de reserva, pago y cancelación',
    'privacidad': 'Política de privacidad', 'cookies': 'Política de cookies', 'centros': 'Condiciones para centros y profesionales',
    'resenas': 'Política de reseñas', 'clasificacion': 'Cómo ordenamos los resultados', 'denuncias': 'Denunciar contenido',
    'seguridad': 'Seguridad en el buceo'}
LEGAL_FIELDS = {'owner_name': 'Titular (nombre y apellidos o razón social)', 'trade_name': 'Nombre comercial', 'nif': 'NIF / CIF',
                'address': 'Domicilio', 'email': 'Email de contacto', 'phone': 'Teléfono', 'registry': 'Datos registrales (si es sociedad)',
                'dpo_email': 'Email para protección de datos', 'hosting': 'Proveedor de alojamiento'}
_LEGAL_CACHE = {}


LEGAL_ALIASES = {'condiciones-buceadores': 'terminos', 'condiciones-centros': 'centros', 'normas-resenas': 'resenas'}


def legal_doc(db, slug, lang='es'):
    """Reads app/legal/<lang>/<slug>.md (falls back to Spanish) and fills in the owner's data from Administración → Legal."""
    slug = LEGAL_ALIASES.get(slug, slug)
    if slug not in LEGAL_DOCS: return None
    lang = 'en' if lang not in ('es',) and (ROOT / 'app' / 'legal' / 'en' / f'{slug}.md').exists() else 'es'
    key = (lang, slug)
    p = ROOT / 'app' / 'legal' / lang / f'{slug}.md'
    try: mt = p.stat().st_mtime
    except OSError: return None
    if key not in _LEGAL_CACHE or _LEGAL_CACHE[key][0] != mt: _LEGAL_CACHE[key] = (mt, p.read_text(encoding='utf-8'))
    text = _LEGAL_CACHE[key][1]
    st = legal_settings(db)
    pending = '[pendiente de completar]' if lang == 'es' else '[to be completed]'
    values = {**{k: (st.get(k) or pending) for k in LEGAL_FIELDS}, 'site_url': public_site_url(),
              'trade_name': st.get('trade_name') or 'WORLDIVES DISCOVERY', 'version': LEGAL_VERSION,
              'hosting': st.get('hosting') or pending, 'dpo_email': st.get('dpo_email') or st.get('email') or pending}
    text = re.sub(r'\{\{(\w+)\}\}', lambda m: str(values.get(m.group(1), m.group(0))), text)
    title = text.split('\n', 1)[0].lstrip('# ').strip()
    return {'slug': slug, 'lang': lang, 'title': title, 'markdown': text, 'version': LEGAL_VERSION}


def booking_start(b):
    """Local date and time of the activity (09:00 when the centre has not set a time)."""
    try:
        t = (b['booking_time'] or '09:00')[:5]
        return datetime.fromisoformat(f"{b['booking_date']}T{t if re.fullmatch(r'\d{2}:\d{2}', t) else '09:00'}")
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Payments (v50.34, Fase 2). Decisions of the owner:
#   · WORLDIVES charges no commission on bookings. Its only income is the annual plan of the centres.
#   · Direct charges: the money goes from the diver to the provider's own Stripe account (centre, or freelance
#     professional without a centre). It never passes through a WORLDIVES balance.
#   · Connected accounts are configured with controller properties (Accounts v1): full Stripe Dashboard for the
#     provider, Stripe fees paid by the provider, Stripe responsible for negative balances, and the provider
#     manages its refunds and disputes. All of it can be changed with environment variables (see .env.example).
# ---------------------------------------------------------------------------
def stripe_controller():
    """Controller properties of the connected accounts WORLDIVES creates."""
    dash = (os.environ.get('WOD_STRIPE_DASHBOARD') or 'full').strip().lower()
    losses = (os.environ.get('WOD_STRIPE_LOSSES') or 'stripe').strip().lower()
    fees = (os.environ.get('WOD_STRIPE_FEES_PAYER') or 'account').strip().lower()
    return {'stripe_dashboard': {'type': dash if dash in ('full', 'express', 'none') else 'full'},
            'fees': {'payer': fees if fees in ('account', 'application') else 'account'},
            'losses': {'payments': losses if losses in ('stripe', 'application') else 'stripe'},
            'requirement_collection': 'stripe'}


def stripe_capabilities():
    caps = [c.strip() for c in (os.environ.get('WOD_STRIPE_CAPABILITIES') or 'card_payments').split(',') if c.strip()]
    return {c: {'requested': True} for c in caps}


PAYEE_CENTER_COLS = ('id,name,email,phone,address,city,country,website,legal_name,tax_id,fiscal_address,stripe_account_id,stripe_charges_enabled,'
                     'stripe_payouts_enabled,stripe_details_submitted,cancellation_policy,cancellation_note,cancel_free_hours,cancel_refund_pct')


def payee_of(db, center_id=None, user_id=None):
    """Who provides the service and receives the money: a centre or a freelance professional without a centre.
    Returns a dict with the same keys for both (type, id, name, contact, fiscal data, Stripe account, policy)."""
    if center_id:
        c = db.execute(f'SELECT {PAYEE_CENTER_COLS} FROM centers WHERE id=?', (center_id,)).fetchone()
        if c: return dict(c, type='center')
    if user_id:
        u = db.execute('''SELECT u.id,u.fullname AS name,u.email,up.phone,NULL AS address,up.city,up.country,NULL AS website,u.legal_name,u.tax_id,u.fiscal_address,
                                 u.stripe_account_id,u.stripe_charges_enabled,u.stripe_payouts_enabled,u.stripe_details_submitted,NULL AS cancellation_policy,
                                 u.cancellation_note,u.cancel_free_hours,u.cancel_refund_pct,u.center_id AS own_center_id
                            FROM users u LEFT JOIN user_profiles up ON up.user_id=u.id WHERE u.id=?''', (user_id,)).fetchone()
        if u:
            if u['own_center_id']: return payee_of(db, u['own_center_id'])
            return dict(u, type='freelance')
    return None


def booking_payee(db, b):
    """The service of a booking and its provider (payee_of)."""
    svc = db.execute('SELECT * FROM provider_services WHERE id=?', (b['service_id'],)).fetchone() if b['service_id'] else None
    keys = b.keys()
    provider = b['provider_user_id'] if 'provider_user_id' in keys else None
    return svc, payee_of(db, b['center_id'], provider or (svc['provider_user_id'] if svc else None))


def payee_ready(p):
    return center_payments_ready(p)


def payee_table(p):
    return 'centers' if p['type'] == 'center' else 'users'


def order_is_direct(order):
    return 'charge_type' in order.keys() and order['charge_type'] == 'direct'


def stripe_kw(order):
    """Direct charges live on the provider's account: every call about them carries stripe_account."""
    return {'stripe_account': order['connected_account_id']} if order_is_direct(order) and order['connected_account_id'] else {}


def stripe_session(order, expand=True):
    stripe = stripe_module()
    return stripe.checkout.Session.retrieve(order['provider_payment_id'], **({'expand': ['payment_intent.latest_charge']} if expand else {}), **stripe_kw(order))


def expire_checkout(order):
    """Closes an open Stripe Checkout so it can no longer be paid (best effort)."""
    if not (stripe_secret() and order['provider_payment_id']): return
    try:
        stripe = stripe_module()
        sess = stripe_session(order, expand=False)
        if _obj(sess, 'status') == 'open': stripe.checkout.Session.expire(order['provider_payment_id'], **stripe_kw(order))
    except Exception as exc:
        sys.stderr.write(f'[pagos] no se pudo cerrar el pago {order["id"]}: {exc}\n')


def order_paid_at_stripe(order):
    """Asks Stripe whether an open Checkout was paid (when the webhook has not arrived yet). Returns the session or None."""
    if not (stripe_secret() and order['provider_payment_id']): return None
    try:
        sess = stripe_session(order)
        return sess if _obj(sess, 'payment_status') in ('paid', 'no_payment_required') else None
    except Exception as exc:
        sys.stderr.write(f'[pagos] consulta del pago {order["id"]}: {exc}\n')
        return None


# Cancellation policy (Fase 2.6): free cancellation until X hours before the activity, then Y % refunded.
# Set by the centre (or freelance) and optionally per service. The policy shown before paying is copied into the
# booking, so later changes never affect bookings already made.
CANCEL_POLICIES = {'flexible': 24, 'moderada': 48, 'estricta': 168}
CANCEL_POLICY_TEXT = {
    'flexible': 'Flexible: cancelación gratuita hasta 24 horas antes de la actividad; después no hay reembolso.',
    'moderada': 'Moderada: cancelación gratuita hasta 48 horas antes de la actividad; después no hay reembolso.',
    'estricta': 'Estricta: cancelación gratuita hasta 7 días antes de la actividad; después no hay reembolso.'}
DEFAULT_CANCEL_HOURS, DEFAULT_CANCEL_PCT = 48, 0


def cancellation_policy_key(policy_value):
    return policy_value if policy_value in CANCEL_POLICIES else 'moderada'


def cancellation_policy_hours(policy_value):
    return CANCEL_POLICIES[cancellation_policy_key(policy_value)]


def clean_policy_numbers(hours, pct):
    """Hours 0–720 (30 days) and refund 0–100 %. None stays None (inherit)."""
    def num(v, lo, hi):
        if v in (None, ''): return None
        try: return max(lo, min(hi, int(round(float(v)))))
        except (TypeError, ValueError): raise ValueError('La política de cancelación necesita números válidos.')
    return num(hours, 0, 720), num(pct, 0, 100)


def policy_text(hours, pct, lang='es'):
    hours, pct = int(hours), int(pct)
    when = (mail_t(lang, '{n} días', n=hours // 24) if hours >= 48 and hours % 24 == 0 else mail_t(lang, '{n} horas', n=hours))
    if hours == 0 and pct == 0: return mail_t(lang, 'Sin cancelación gratuita: no hay reembolso al cancelar.')
    if hours == 0: return mail_t(lang, 'Al cancelar se devuelve el {pct} % de lo pagado.', pct=pct)
    after = mail_t(lang, 'después no hay reembolso.') if pct == 0 else (mail_t(lang, 'después se devuelve el {pct} % de lo pagado.', pct=pct) if pct < 100 else mail_t(lang, 'después también se devuelve todo.'))
    return mail_t(lang, 'Cancelación gratuita hasta {when} antes de la actividad; {after}', when=when, after=after)


def cancellation_policy_text(policy_value, lang='es'):
    """Text of one of the three presets (kept for old callers)."""
    return mail_t(lang, CANCEL_POLICY_TEXT[cancellation_policy_key(policy_value)])


def provider_policy(payee, svc=None):
    """Policy that applies to a new booking: the service's if it has one, else the provider's, else 48 h / 0 %."""
    hours = pct = None
    if svc is not None and 'cancel_free_hours' in svc.keys():
        hours, pct = svc['cancel_free_hours'], svc['cancel_refund_pct']
    if hours is None and payee:
        hours = payee.get('cancel_free_hours')
        if hours is None and payee.get('cancellation_policy'): hours = cancellation_policy_hours(payee['cancellation_policy'])
    if pct is None and payee: pct = payee.get('cancel_refund_pct')
    hours = DEFAULT_CANCEL_HOURS if hours is None else int(hours)
    pct = DEFAULT_CANCEL_PCT if pct is None else int(pct)
    return {'free_hours': hours, 'refund_pct': pct, 'text': policy_text(hours, pct), 'note': (payee or {}).get('cancellation_note') or ''}


def booking_policy(db, b, lang='es'):
    """The policy of an existing booking (its own copy; old bookings without a copy use the provider's)."""
    keys = b.keys()
    if 'cancel_free_hours' in keys and b['cancel_free_hours'] is not None:
        hours, pct = int(b['cancel_free_hours']), int(b['cancel_refund_pct'] or 0)
        svc, payee = booking_payee(db, b)
        return {'free_hours': hours, 'refund_pct': pct, 'text': policy_text(hours, pct, lang), 'note': (payee or {}).get('cancellation_note') or ''}
    svc, payee = booking_payee(db, b)
    p = provider_policy(payee, svc)
    if lang != 'es': p['text'] = policy_text(p['free_hours'], p['refund_pct'], lang)
    return p


def booking_paid_online(db, bid):
    """What the diver has paid online for a booking, net of refunds, and the orders it came from."""
    orders = db.execute("SELECT * FROM payment_orders WHERE booking_id=? AND status IN ('paid','partially_refunded','refunded') ORDER BY id", (bid,)).fetchall()
    paid = sum(float(o['amount_received'] or o['amount'] or 0) for o in orders)
    refunded = sum(float(o['refunded_total'] or 0) for o in orders)
    return round(paid, 2), round(refunded, 2), orders


def booking_cancel_terms(db, b):
    """What happens if the diver cancels now: refund proposed by the provider's policy and the free-cancellation deadline."""
    pol = booking_policy(db, b); hours = pol['free_hours']
    start = booking_start(b); left = (start - datetime.now()).total_seconds() / 3600 if start else 0
    paid, refunded, orders = booking_paid_online(db, b['id'])
    net = max(0.0, paid - refunded)
    free = left >= hours
    amount = net if free else round(net * pol['refund_pct'] / 100, 2)
    deadline = (start - _timedelta(hours=hours)).isoformat(timespec='minutes') if start else None
    return {'policy': f'{hours}h-{pol["refund_pct"]}', 'policy_hours': hours, 'refund_pct': pol['refund_pct'], 'hours_left': round(left, 1), 'free': free,
            'paid_online': bool(orders), 'refund_amount': round(amount, 2), 'paid_amount': round(net, 2), 'deadline': deadline,
            'started': left <= 0, 'policy_text': pol['text']}


def deposit_for(svc, price, participants):
    """Deposit («señal») charged online for a service, or None when the whole price is paid online.
    Percentage of the total, or a fixed amount per person. Never more than the price."""
    if not svc or price <= 0 or 'deposit_type' not in svc.keys(): return None
    kind, value = svc['deposit_type'] or 'none', float(svc['deposit_value'] or 0)
    if kind == 'percent' and 0 < value < 100: amount = round(price * value / 100, 2)
    elif kind == 'fixed' and value > 0: amount = round(value * max(1, int(participants or 1)), 2)
    else: return None
    return amount if 0 < amount < price else None


def clean_deposit(data, price):
    kind = clean_text(data.get('deposit_type'), 10) or 'none'
    if kind not in ('none', 'percent', 'fixed'): kind = 'none'
    value = None
    if kind != 'none':
        try: value = round(float(str(data.get('deposit_value') or '0').replace(',', '.')), 2)
        except ValueError: raise ValueError('La señal debe ser un número.')
        if kind == 'percent' and not 0 < value < 100: raise ValueError('La señal en porcentaje debe estar entre 1 y 99 %.')
        if kind == 'fixed' and not 0 < value: raise ValueError('Indica el importe de la señal por persona.')
        if kind == 'fixed' and price and value >= price: raise ValueError('La señal por persona debe ser menor que el precio.')
    return kind, value


# Refunds (Fase 2.4): started by the provider from its panel, total or partial, on its own Stripe account.
# A partial refund never cancels the booking. Refunds made in the Stripe Dashboard arrive by webhook.
def recompute_order_refunds(db, order_id):
    o = db.execute('SELECT * FROM payment_orders WHERE id=?', (order_id,)).fetchone()
    if not o: return
    total = db.execute("SELECT COALESCE(SUM(amount),0) FROM payment_refunds WHERE payment_order_id=? AND status IN ('succeeded','pending')", (order_id,)).fetchone()[0] or 0
    paid = float(o['amount_received'] or o['amount'] or 0)
    total = round(min(paid, float(total)), 2)
    status = o['status']
    if o['status'] in ('paid', 'partially_refunded', 'refunded'):
        status = 'refunded' if total >= paid - 0.005 and total > 0 else ('partially_refunded' if total > 0 else 'paid')
    db.execute('UPDATE payment_orders SET refunded_total=?,refund_amount=?,status=?,refunded_at=CASE WHEN ?>0 THEN COALESCE(refunded_at,?) ELSE refunded_at END,updated_at=? WHERE id=?',
               (total, total, status, total, now(), now(), order_id))
    if o['booking_id']:
        bid = o['booking_id']
        paid_b, refunded_b, orders = booking_paid_online(db, bid)
        b = booking_row(db, bid)
        pay = b['payment_status']
        if refunded_b > 0: pay = 'refunded' if refunded_b >= paid_b - 0.005 else 'partially_refunded'
        proposal = b['refund_status']
        if proposal == 'proposed' and refunded_b >= float(b['refund_proposed'] or 0) - 0.005: proposal = 'done'
        db.execute('UPDATE bookings SET refunded_total=?,refund_amount=?,payment_status=?,refund_status=?,updated_at=? WHERE id=?', (refunded_b, refunded_b, pay, proposal, now(), bid))
    if o['experience_booking_id']:
        db.execute('UPDATE experience_bookings SET refunded_total=?,updated_at=? WHERE id=?', (total, now(), o['experience_booking_id']))


def upsert_refund(db, order, stripe_refund_id, amount, status, source, reason=None, note=None, actor=None):
    """Records one refund (idempotent by its Stripe id) and recomputes the totals of the order and the booking."""
    st = {'succeeded': 'succeeded', 'pending': 'pending', 'requires_action': 'pending', 'failed': 'failed', 'canceled': 'failed'}.get(status, 'pending')
    row = db.execute('SELECT id FROM payment_refunds WHERE stripe_refund_id=?', (stripe_refund_id,)).fetchone() if stripe_refund_id else None
    if row:
        db.execute('UPDATE payment_refunds SET status=?,amount=?,updated_at=? WHERE id=?', (st, amount, now(), row['id']))
    else:
        db.execute('''INSERT INTO payment_refunds(payment_order_id,booking_id,experience_booking_id,amount,currency,reason,note,stripe_refund_id,status,source,created_by,created_at,updated_at)
                      VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)''', (order['id'], order['booking_id'], order['experience_booking_id'], amount, order['currency'] or 'EUR', reason, note,
                                                             stripe_refund_id, st, source, actor, now(), now()))
    recompute_order_refunds(db, order['id'])


def refund_payment(db, order, amount, reason='requested_by_customer', actor=None, note='', source='panel'):
    """Refunds part or all of a paid order through Stripe, on the provider's account for direct charges.
    Raises ValueError with a clear message when it cannot. Returns the refunded amount."""
    paid = float(order['amount_received'] or order['amount'] or 0)
    left = round(paid - float(order['refunded_total'] or 0), 2)
    amount = round(float(amount), 2)
    if amount <= 0: raise ValueError('Indica un importe mayor que cero.')
    if amount > left + 0.005: raise ValueError(f'Solo quedan {left:.2f} {order["currency"] or "EUR"} por devolver de este pago.')
    if not stripe_secret(): raise ValueError('Los cobros online no están configurados en el servidor.')
    pi = order['payment_intent_id'] if 'payment_intent_id' in order.keys() else None
    stripe = stripe_module()
    if not pi and order['provider_payment_id']:
        sess = stripe_session(order, expand=False)
        p_ = _obj(sess, 'payment_intent'); pi = p_ if isinstance(p_, str) or p_ is None else _obj(p_, 'id')
        if pi: db.execute('UPDATE payment_orders SET payment_intent_id=? WHERE id=?', (pi, order['id']))
    if not pi: raise ValueError('Este pago no tiene referencia de Stripe: devuélvelo desde tu panel de Stripe.')
    cents = int(round(amount * 100)); done = int(round(float(order['refunded_total'] or 0) * 100))
    params = dict(payment_intent=pi, amount=cents, reason=reason if reason in ('duplicate', 'fraudulent', 'requested_by_customer') else 'requested_by_customer',
                  metadata={'payment_order_id': str(order['id']), 'booking_id': str(order['booking_id'] or ''), 'wod_reason': str(reason)[:40]},
                  idempotency_key=f'wod-refund-{order["id"]}-{done}-{cents}')
    if order_is_direct(order): params.update(stripe_kw(order))
    else:  # orders of v50.33 and earlier were destination charges with an application fee
        params.update(reverse_transfer=True, refund_application_fee=abs(amount - left) < 0.005)
    try:
        ref = stripe.Refund.create(**params)
    except Exception as exc:
        sys.stderr.write(f'[pagos] devolución del pedido {order["id"]}: {exc}\n')
        audit(db, actor, 'payment_refund_failed', 'payment_order', order['id'], {'amount': amount, 'error': str(exc)[:200]})
        raise ValueError('Stripe no ha aceptado la devolución: ' + (getattr(exc, 'user_message', None) or str(exc))[:200])
    upsert_refund(db, order, _obj(ref, 'id'), amount, _obj(ref, 'status') or 'pending', source, reason, clean_text(note, 300), actor)
    audit(db, actor, 'payment_refunded', 'payment_order', order['id'], {'amount': amount, 'reason': reason, 'source': source})
    return amount


def refund_booking(db, bid, amount=None, reason='requested_by_customer', actor=None, note='', source='panel'):
    """Refunds a booking's online payments (newest first) up to amount (None = everything still refundable).
    Returns 'none_paid' | 'refunded' | 'refund_pending' | 'no_refund'."""
    paid, refunded, orders = booking_paid_online(db, bid)
    if not orders: return 'none_paid'
    left = round(paid - refunded, 2)
    want = left if amount is None else min(left, round(float(amount), 2))
    if want <= 0: return 'no_refund'
    try:
        for o in reversed(orders):
            o = db.execute('SELECT * FROM payment_orders WHERE id=?', (o['id'],)).fetchone()
            avail = round(float(o['amount_received'] or o['amount'] or 0) - float(o['refunded_total'] or 0), 2)
            if avail <= 0 or want <= 0: continue
            part = min(avail, want)
            refund_payment(db, o, part, reason, actor, note, source); want = round(want - part, 2)
        return 'refunded'
    except ValueError as exc:
        db.execute("UPDATE bookings SET refund_status='failed',refund_proposed=COALESCE(refund_proposed,?),refund_proposed_at=COALESCE(refund_proposed_at,?),updated_at=? WHERE id=?",
                   (want, now(), now(), bid))
        notify_booking(db, bid, 'refund_failed', {'error': str(exc)[:200]})
        return 'refund_pending'


def refund_paid_booking(db, bid, amount=None, reason='requested_by_customer'):
    """Kept for old callers: refunds through refund_booking."""
    return refund_booking(db, bid, amount, reason, source='system')


def propose_refund(db, b, amount, why):
    """The diver cancelled a paid booking: the refund that the provider's policy gives is proposed to the provider,
    who sends it from its panel (it manages its own refunds). Reminded by email if it is still pending after 72 h."""
    db.execute("UPDATE bookings SET refund_proposed=?,refund_status=?,refund_proposed_at=?,updated_at=? WHERE id=?",
               (round(amount, 2), 'proposed' if amount > 0 else 'none', now(), now(), b['id']))
    audit(db, None, 'refund_proposed', 'booking', b['id'], {'amount': round(amount, 2), 'why': why})


def run_refund_reminders(db):
    """Maintenance job: providers are reminded once of proposed refunds still pending after 72 hours."""
    limit = (datetime.now(timezone.utc) - _timedelta(hours=72)).isoformat(timespec='seconds')
    for b in db.execute("SELECT id FROM bookings WHERE refund_status='proposed' AND refund_proposed_at<? AND refund_reminded_at IS NULL LIMIT 200", (limit,)).fetchall():
        notify_booking(db, b['id'], 'refund_reminder')
        db.execute('UPDATE bookings SET refund_reminded_at=? WHERE id=?', (now(), b['id'])); db.commit()


def can_manage_booking(user, b):
    """The provider of a booking: its centre (owner and team), or the freelance professional when it has no centre."""
    if not user: return False
    if user['role'] == 'admin': return True
    if user['role'] == 'center': return bool(user['center_id']) and b['center_id'] == user['center_id']
    if user['role'] == 'freelance':
        prov = b['provider_user_id'] if 'provider_user_id' in b.keys() else None
        return not b['center_id'] and prov == user['id']
    return False


def require_booking_provider(user, b):
    if not can_manage_booking(user, b):
        raise PermissionError('Esta reserva no pertenece a tu centro.' if user['role'] == 'center' else 'No puedes gestionar esta reserva.')


def provider_scope_sql(user, alias='b'):
    """WHERE fragment for the bookings a provider manages (centre or freelance without centre)."""
    if user['role'] == 'center' and user['center_id']: return f'{alias}.center_id=?', [int(user['center_id'])]
    if user['role'] == 'freelance': return f'({alias}.center_id IS NULL AND {alias}.provider_user_id=?)', [user['id']]
    raise PermissionError('Solo los centros y profesionales gestionan reservas.')


def release_booking_spots(db, b):
    if b['slot_id'] and b['slot_reserved']:
        release_slot_spots(db, b['slot_id'], max(1, int(b['participants'] or 1)))
        db.execute('UPDATE bookings SET slot_reserved=0 WHERE id=?', (b['id'],))


# ---------------------------------------------------------------------------
# Booking flow (v50.32, Fase 1B). Two modes and one state machine (wod.bookings):
#   «Pago al reservar»: payment_in_progress (spots held HOLD_MINUTES) → confirmed when Stripe confirms the payment.
#   «Bajo petición»: requested → accepted_pending_payment (spots held, pay before the deadline) → confirmed
#                    or requested → confirmed (no online payments / free) · rejected · expired.
# There is no path that confirms a «Pago al reservar» booking with a price without a payment confirmed by Stripe.
# Times are local wall-clock times (as booking dates and times are).
# ---------------------------------------------------------------------------
HOLD_MINUTES = wcfg.env_int('WOD_PAYMENT_HOLD_MINUTES', wbk.DEFAULT_HOLD_MINUTES, 5, 60)


def local_now():
    return datetime.now().replace(microsecond=0)


def local_iso(dt):
    return dt.replace(microsecond=0).isoformat(timespec='minutes') if dt else None


def parse_local(value):
    try: return datetime.fromisoformat(str(value)) if value else None
    except ValueError: return None


def service_payments_ready(db, svc):
    """Can this service's provider take card payments right now? Centres: their Stripe Connect account.
    Freelance professionals without a centre: their own connected account (Fase 2)."""
    if not svc: return False
    center_id = svc['center_id'] if 'center_id' in (svc.keys() if hasattr(svc, 'keys') else svc) else None
    if center_id:
        c = db.execute('SELECT stripe_account_id,stripe_charges_enabled,stripe_payouts_enabled FROM centers WHERE id=?', (center_id,)).fetchone()
        return center_payments_ready(c)
    try:
        u = db.execute('SELECT stripe_account_id,stripe_charges_enabled,stripe_payouts_enabled FROM users WHERE id=?', (svc['provider_user_id'],)).fetchone()
    except sqlite3.OperationalError:
        return False
    return center_payments_ready(u)


def service_mode_info(db, svc, price=None, ready=None):
    """What the diver sees for a service: mode, its label, whether it can be booked now and the button text."""
    mode = 'payment' if svc['booking_mode'] == 'payment' else 'request'
    ready = service_payments_ready(db, svc) if ready is None else ready
    hours = wbk.clamp_hours(svc['response_hours'] if 'response_hours' in svc.keys() else None, wbk.DEFAULT_RESPONSE_HOURS)
    info = {'booking_mode': mode, 'mode_label': wbk.mode_label(mode, hours), 'response_hours': hours, 'payments_ready': bool(ready), 'bookable': True,
            'instant': mode == 'payment' and bool(ready)}
    if mode == 'payment' and not ready:
        info.update(bookable=False, unavailable_reason='Este servicio se reserva pagando online y ahora mismo no admite reservas.')
    return info


def booking_view_status(b):
    """Status text shared by «Mis reservas», the panel, emails and PDFs."""
    d = {'status': wbk.normalize_state(b['status']), 'status_label': wbk.state_label(b['status'])}
    reason = b['expired_reason'] if 'expired_reason' in b.keys() else None
    if d['status'] == 'expired':
        d['status_label'] = {'hold_expired': 'Caducada · no pagada', 'payment_cancelled': 'Caducada · no pagada', 'checkout_failed': 'Caducada · no pagada',
                             'no_response': 'Caducada · el centro no respondió a tiempo', 'not_paid': 'Caducada · no se pagó a tiempo'}.get(reason, 'Caducada')
    return d


def reserve_or_fail(db, b):
    if b['slot_id'] and not b['slot_reserved']:
        if not reserve_slot_spots(db, b['slot_id'], max(1, int(b['participants'] or 1))):
            raise ValueError('No quedan plazas suficientes en esa salida.')
        db.execute('UPDATE bookings SET slot_reserved=1 WHERE id=?', (b['id'],))


def booking_row(db, bid):
    return db.execute('SELECT * FROM bookings WHERE id=?', (bid,)).fetchone()


def accept_booking(db, actor, b):
    """The provider accepts a request. Spots are taken now; if it charges online the diver gets a deadline to pay."""
    if b['status'] not in ('requested', 'pending'): raise ValueError('Esta solicitud ya no está pendiente.')
    dl = parse_local(b['response_deadline'])
    if dl and local_now() > dl: raise ValueError('El plazo para responder a esta solicitud ha terminado.')
    reserve_or_fail(db, b)
    svc = db.execute('SELECT * FROM provider_services WHERE id=?', (b['service_id'],)).fetchone() if b['service_id'] else None
    price = float(b['price'] or 0)
    ready = service_payments_ready(db, svc) if svc else center_payments_ready(db.execute('SELECT stripe_account_id,stripe_charges_enabled,stripe_payouts_enabled FROM centers WHERE id=?', (b['center_id'],)).fetchone())
    if price > 0 and ready and b['payment_status'] != 'paid':
        hours = wbk.clamp_hours(svc['payment_hours'] if svc else None, wbk.DEFAULT_PAYMENT_HOURS)
        deadline = wbk.deadline_before_start(local_now(), hours, wbk.activity_start(b['booking_date'], b['booking_time']))
        db.execute("UPDATE bookings SET status='accepted_pending_payment',payment_status='required',payment_deadline=?,accepted_at=?,decided_by=?,updated_at=? WHERE id=?",
                   (local_iso(deadline), now(), actor['id'] if actor else None, now(), b['id']))
        notify_booking(db, b['id'], 'accepted_payment')
        return 'accepted_pending_payment'
    pay = 'paid' if b['payment_status'] == 'paid' else ('at_center' if price > 0 else 'not_required')
    db.execute("UPDATE bookings SET status='confirmed',payment_status=?,accepted_at=?,confirmed_at=?,decided_by=?,updated_at=? WHERE id=?",
               (pay, now(), now(), actor['id'] if actor else None, now(), b['id']))
    notify_booking(db, b['id'], 'confirmed')
    return 'confirmed'


def reject_booking(db, actor, b, reason=''):
    if b['status'] not in ('requested', 'pending', 'accepted_pending_payment'): raise ValueError('Esta solicitud ya no se puede rechazar.')
    release_booking_spots(db, b)
    db.execute("UPDATE bookings SET status='rejected',reject_reason=?,decided_by=?,cancelled_at=?,cancelled_by='center',updated_at=? WHERE id=?",
               (clean_text(reason, 500) or None, actor['id'] if actor else None, now(), now(), b['id']))
    for o in db.execute("SELECT * FROM payment_orders WHERE booking_id=? AND status='pending'", (b['id'],)).fetchall():
        expire_checkout(o); db.execute("UPDATE payment_orders SET status='cancelled',updated_at=? WHERE id=?", (now(), o['id']))
    outcome = refund_booking(db, b['id'], None, 'requested_by_customer', actor['id'] if actor else None, 'Solicitud rechazada', 'reject')
    notify_booking(db, b['id'], 'rejected', {'refund': outcome, 'reason': clean_text(reason, 500) or ''})
    return outcome


def expire_booking(db, b, reason, notify=True):
    """A deadline has passed: release the spots and mark the booking as expired («caducada»)."""
    for o in db.execute("SELECT * FROM payment_orders WHERE booking_id=? AND status='pending'", (b['id'],)).fetchall():
        sess = order_paid_at_stripe(o)
        if sess:
            finalize_paid_order(db, o, sess, 'deadline-check'); return 'paid'
        expire_checkout(o); db.execute("UPDATE payment_orders SET status='expired',updated_at=? WHERE id=?", (now(), o['id']))
    release_booking_spots(db, b)
    db.execute("UPDATE bookings SET status='expired',expired_reason=?,payment_status=CASE WHEN payment_status IN ('required','pending') THEN 'not_paid' ELSE payment_status END,updated_at=? WHERE id=?",
               (reason, now(), b['id']))
    audit(db, None, 'booking_expired', 'booking', b['id'], {'reason': reason})
    if notify and reason in ('no_response', 'not_paid'): notify_booking(db, b['id'], 'expired_' + reason)
    return 'expired'


def run_booking_deadlines(db):
    """Every minute: payment holds, response deadlines and payment deadlines (Fase 1B)."""
    now_l = local_iso(local_now())
    for b in db.execute("SELECT * FROM bookings WHERE status='payment_in_progress' AND hold_expires_at IS NOT NULL AND hold_expires_at<? LIMIT 500", (now_l,)).fetchall():
        expire_booking(db, b, 'hold_expired'); db.commit()
    for b in db.execute("SELECT * FROM bookings WHERE status IN ('requested','pending') AND response_deadline IS NOT NULL AND response_deadline<? LIMIT 500", (now_l,)).fetchall():
        expire_booking(db, b, 'no_response'); db.commit()
    for b in db.execute("SELECT * FROM bookings WHERE status='accepted_pending_payment' AND payment_deadline IS NOT NULL AND payment_deadline<? LIMIT 500", (now_l,)).fetchall():
        expire_booking(db, b, 'not_paid'); db.commit()


def _open_order(db, where, args):
    o = db.execute(f"SELECT * FROM payment_orders WHERE {where} AND status='pending' AND checkout_url IS NOT NULL ORDER BY id DESC LIMIT 1", args).fetchone()
    if not o: return None
    try: age = datetime.now(timezone.utc).timestamp() - datetime.fromisoformat(o['created_at']).timestamp()
    except Exception: age = 9999
    return o if age < 25 * 60 else None


def order_for_stripe_object(db, obj, account=None):
    """The payment order a Stripe object belongs to: by our metadata, else by its PaymentIntent or Checkout id."""
    meta = obj.get('metadata') or {}
    oid = int(meta.get('payment_order_id') or 0) if str(meta.get('payment_order_id') or '').isdigit() else 0
    order = db.execute('SELECT * FROM payment_orders WHERE id=?', (oid,)).fetchone() if oid else None
    if not order:
        pi = obj.get('payment_intent') if obj.get('object') != 'payment_intent' else obj.get('id')
        if isinstance(pi, dict): pi = pi.get('id')
        if pi: order = db.execute('SELECT * FROM payment_orders WHERE payment_intent_id=? ORDER BY id DESC LIMIT 1', (pi,)).fetchone()
    if not order and obj.get('object') == 'checkout.session':
        order = db.execute('SELECT * FROM payment_orders WHERE provider_payment_id=?', (obj.get('id'),)).fetchone()
    if order and account and order['connected_account_id'] and order['connected_account_id'] != account:
        return None  # an event of another connected account can never touch this order
    return order


def sync_refunds_from_stripe(db, order, charge=None):
    """Brings every refund of a payment (also those made by the provider in its Stripe Dashboard) into payment_refunds."""
    refunds = ((charge or {}).get('refunds') or {}).get('data') if charge else None
    if refunds is None and stripe_secret() and order['payment_intent_id']:
        try:
            refunds = stripe_module().Refund.list(payment_intent=order['payment_intent_id'], limit=100, **stripe_kw(order)).get('data', [])
        except Exception as exc:
            sys.stderr.write(f'[pagos] lista de devoluciones del pedido {order["id"]}: {exc}\n'); refunds = []
    for r in refunds or []:
        upsert_refund(db, order, r.get('id'), int(r.get('amount') or 0) / 100, r.get('status') or 'succeeded', 'stripe', (r.get('metadata') or {}).get('wod_reason') or r.get('reason'))


def payee_account_updated(db, obj):
    """account.updated: the provider's account can (or can no longer) charge cards."""
    account_id = obj.get('id')
    if not account_id: return
    flags = (1 if obj.get('charges_enabled') else 0, 1 if obj.get('payouts_enabled') else 0, 1 if obj.get('details_submitted') else 0, now(), account_id)
    db.execute('UPDATE centers SET stripe_charges_enabled=?,stripe_payouts_enabled=?,stripe_details_submitted=?,updated_at=? WHERE stripe_account_id=?', flags)
    db.execute('UPDATE users SET stripe_charges_enabled=?,stripe_payouts_enabled=?,stripe_details_submitted=? WHERE stripe_account_id=?', flags[:3] + flags[4:])
    if not (obj.get('charges_enabled') and obj.get('payouts_enabled')):
        for c_ in db.execute('SELECT id FROM centers WHERE stripe_account_id=?', (account_id,)).fetchall(): warn_payment_mode_without_payments(db, c_['id'])
        for u_ in db.execute("SELECT id FROM users WHERE stripe_account_id=? AND role='freelance'", (account_id,)).fetchall(): warn_payment_mode_without_payments(db, None, u_['id'])


def handle_stripe_event(db, event, connect=False):
    """One place for the events of both webhooks (platform and Connect). Idempotent by event id."""
    event_id = event.get('id'); event_type = event.get('type', ''); account = event.get('account') if connect else None
    if event_id:
        try:
            db.execute('INSERT INTO stripe_webhook_events(event_id,event_type,created_at) VALUES(?,?,?)', (event_id, event_type, now()))
        except sqlite3.IntegrityError:
            return 'duplicate'
    obj = (event.get('data') or {}).get('object') or {}
    if event_type in ('account.updated',):
        payee_account_updated(db, obj); return 'ok'
    if event_type == 'account.application.deauthorized' and account:
        payee_account_updated(db, {'id': account}); return 'ok'
    order = order_for_stripe_object(db, obj, account)
    if not order:
        if connect and account and obj.get('metadata', {}).get('platform') == 'worldives':
            audit(db, None, 'stripe_event_without_order', 'stripe_event', None, {'type': event_type, 'account': account})
        return 'ignored'
    oid = order['id']
    if event_type in ('checkout.session.completed', 'checkout.session.async_payment_succeeded'):
        if order['status'] == 'pending':
            sess = obj
            try:
                if stripe_secret(): sess = stripe_session(order)
            except Exception: sess = obj
            finalize_paid_order(db, order, sess, 'webhook')
    elif event_type in ('checkout.session.expired', 'checkout.session.async_payment_failed'):
        if order['status'] == 'pending':
            release_order_hold(db, order, 'expired')
            audit(db, order['user_id'], 'payment_expired', 'payment_order', oid, {'provider': 'stripe', 'event_id': event_id})
    elif event_type == 'payment_intent.payment_failed':
        if order['status'] == 'pending': db.execute("UPDATE payment_orders SET status='failed',updated_at=? WHERE id=?", (now(), oid))
    elif event_type == 'charge.refunded':
        sync_refunds_from_stripe(db, order, obj)
        audit(db, order['user_id'], 'payment_refund_synced', 'payment_order', oid, {'event_id': event_id})
    elif event_type in ('refund.created', 'refund.updated', 'charge.refund.updated'):
        upsert_refund(db, order, obj.get('id'), int(obj.get('amount') or 0) / 100, obj.get('status') or 'pending', 'stripe', (obj.get('metadata') or {}).get('wod_reason') or obj.get('reason'))
    elif event_type in ('charge.dispute.created', 'charge.dispute.closed'):
        closed = event_type.endswith('closed')
        db.execute('UPDATE payment_orders SET incident=?,incident_note=?,incident_at=?,updated_at=? WHERE id=?',
                   ('dispute_closed' if closed else 'dispute', f"Disputa {obj.get('status') or ''} · {obj.get('reason') or ''}".strip(), now(), now(), oid))
        audit(db, None, 'payment_dispute', 'payment_order', oid, {'status': obj.get('status'), 'reason': obj.get('reason')})
        if not closed and order['booking_id']: notify_booking(db, order['booking_id'], 'dispute', {'reason': obj.get('reason') or ''})
    return 'ok'


def stripe_webhook(handler, db, secret_env, connect):
    length = body_length(handler, wcfg.MAX_WEBHOOK_BYTES); raw = handler.rfile.read(length); secret = os.environ.get(secret_env, '').strip()
    if not secret: handler.send_json({'error': 'Webhook no configurado.'}, 503); return
    try:
        event = stripe_module().Webhook.construct_event(raw, handler.headers.get('Stripe-Signature', ''), secret)
    except ImportError: handler.send_json({'error': 'Falta instalar stripe.'}, 500); return
    except Exception: handler.send_json({'error': 'Firma de webhook no válida.'}, 400); return
    if hasattr(event, 'to_dict_recursive'): event = event.to_dict_recursive()
    elif hasattr(event, 'to_dict'): event = event.to_dict()
    out = handle_stripe_event(db, event, connect)
    db.commit()
    handler.send_json({'received': True, 'duplicate': out == 'duplicate'})


COUNTRY_ISO = {'españa': 'ES', 'spain': 'ES', 'portugal': 'PT', 'francia': 'FR', 'france': 'FR', 'italia': 'IT', 'italy': 'IT', 'alemania': 'DE', 'germany': 'DE',
               'grecia': 'GR', 'greece': 'GR', 'croacia': 'HR', 'croatia': 'HR', 'malta': 'MT', 'chipre': 'CY', 'cyprus': 'CY', 'países bajos': 'NL', 'netherlands': 'NL',
               'bélgica': 'BE', 'belgium': 'BE', 'polonia': 'PL', 'poland': 'PL', 'reino unido': 'GB', 'united kingdom': 'GB', 'irlanda': 'IE', 'ireland': 'IE',
               'méxico': 'MX', 'mexico': 'MX', 'estados unidos': 'US', 'united states': 'US', 'egipto': 'EG', 'tailandia': 'TH', 'indonesia': 'ID', 'filipinas': 'PH'}


def self_payee(db, user, data):
    """The payee a signed-in provider manages: its centre, or itself as freelance. The admin names one."""
    if user['role'] == 'center':
        p = payee_of(db, user['center_id']) if user['center_id'] else None
    elif user['role'] == 'freelance':
        p = payee_of(db, None, user['id'])
    else:
        cid = int(data.get('center_id') or 0); uid = int(data.get('user_id') or 0)
        p = payee_of(db, cid) if cid else (payee_of(db, None, uid) if uid else None)
    if not p: raise ValueError('Centro o profesional no válido.')
    return p


def create_stripe_checkout(db, user, *, amount, currency, title, payee, booking_id=None, experience_booking_id=None, provider_user_id=None,
                           service_id=None, slot_id=None, cancel_url, hold_reserved=False, kind='full', description=None):
    """Creates the payment order and its Stripe Checkout Session as a DIRECT charge on the provider's connected
    account (no application fee, no transfer: WORLDIVES takes no commission). Raises ValueError when it cannot."""
    if amount <= 0: raise ValueError('Esta reserva no tiene un importe que pagar online.')
    secret = stripe_secret(); base = public_site_url()
    if not secret: raise ValueError('El pago seguro aún no está configurado en el servidor.')
    if not payee or not payee_ready(payee): raise ValueError('El prestador no tiene ahora mismo los cobros online activos.')
    account_id = payee['stripe_account_id']
    oid = db.execute('''INSERT INTO payment_orders(user_id,provider_user_id,booking_id,experience_booking_id,service_id,slot_id,amount,currency,status,provider,platform_fee,
                         connected_account_id,charge_type,payment_kind,payee_type,payee_id,hold_reserved,created_at,updated_at)
                         VALUES(?,?,?,?,?,?,?,?,'pending','stripe',0,?,'direct',?,?,?,?,?,?)''',
                     (user['id'], provider_user_id, booking_id, experience_booking_id, service_id, slot_id, amount, currency, account_id, kind, payee['type'], payee['id'],
                      1 if hold_reserved else 0, now(), now())).lastrowid
    db.commit()
    ref = f'WOD-{int(booking_id):06d}' if booking_id else f'EXP-{int(experience_booking_id or 0):05d}'
    meta = {'payment_order_id': str(oid), 'booking_id': str(booking_id or ''), 'experience_booking_id': str(experience_booking_id or ''), 'platform': 'worldives'}
    try:
        stripe = stripe_module()
        session = stripe.checkout.Session.create(
            mode='payment',
            line_items=[{'price_data': {'currency': currency.lower(), 'product_data': {'name': title[:250], 'description': (description or f'{ref} · {payee["name"]}')[:500]},
                                        'unit_amount': int(round(amount * 100))}, 'quantity': 1}],
            success_url=f'{base}/#/pago-ok?session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=cancel_url,
            metadata=meta,
            payment_intent_data={'description': f'{ref} · {payee["name"]}'[:500], 'metadata': meta},
            client_reference_id=f'WOD-{oid}',
            customer_email=user['email'] if mail_deliverable(user['email']) else None,
            expires_at=int(time.time()) + 30 * 60, locale='auto',
            stripe_account=account_id,
            idempotency_key=f'wod-checkout-{oid}')
    except ImportError:
        db.execute("UPDATE payment_orders SET status='failed',updated_at=? WHERE id=?", (now(), oid)); db.commit()
        raise ValueError('Falta instalar la dependencia stripe en el servidor.')
    except Exception as exc:
        db.execute("UPDATE payment_orders SET status='failed',updated_at=? WHERE id=?", (now(), oid)); db.commit()
        sys.stderr.write(f'[pagos] Stripe rechazó el pedido {oid}: {exc}\n')
        raise ValueError('No se ha podido abrir el pago seguro. Inténtalo de nuevo en unos minutos.')
    db.execute('UPDATE payment_orders SET provider_payment_id=?,checkout_url=?,updated_at=? WHERE id=?', (session.id, session.url, now(), oid)); db.commit()
    return {'checkout_url': session.url, 'order_id': oid}


def start_checkout(db, user, b):
    """Opens the payment of a booking in its two legal moments (Fase 1B): the whole price or the deposit (Fase 2.5)."""
    st = wbk.normalize_state(b['status'])
    if b['payment_status'] in ('paid', 'deposit_paid'): raise ValueError('Esta reserva ya está pagada.')
    if st == 'payment_in_progress':
        hold = parse_local(b['hold_expires_at'])
        if hold and local_now() > hold: raise ValueError('El tiempo para pagar esta reserva ha terminado y las plazas se han liberado. Vuelve a reservar.')
    elif st == 'accepted_pending_payment':
        dl = parse_local(b['payment_deadline'])
        if dl and local_now() > dl: raise ValueError('El plazo para pagar esta reserva ha terminado.')
    elif st == 'requested': raise ValueError('El centro todavía no ha aceptado esta solicitud. No se cobra nada hasta entonces.')
    else: raise ValueError('Esta reserva no tiene ningún pago pendiente.')
    reuse = _open_order(db, 'booking_id=?', (b['id'],))
    if reuse: return {'checkout_url': reuse['checkout_url'], 'order_id': reuse['id'], 'reused': True}
    svc, payee = booking_payee(db, b)
    if not payee_ready(payee):
        raise ValueError('El centro no tiene ahora mismo los cobros online activos. Contacta con el centro.')
    price = float(b['price'] or 0); currency = b['currency'] or 'EUR'
    deposit = float(b['deposit_amount'] or 0) if 'deposit_amount' in b.keys() else 0
    amount, kind = (deposit, 'deposit') if 0 < deposit < price else (price, 'full')
    title = (svc['title'] if svc else 'Reserva de buceo') + (' · señal' if kind == 'deposit' else '')
    return create_stripe_checkout(db, user, amount=amount, currency=currency, title=title, payee=payee, kind=kind,
                                  provider_user_id=svc['provider_user_id'] if svc else None, booking_id=b['id'],
                                  service_id=b['service_id'], slot_id=b['slot_id'], hold_reserved=bool(b['slot_reserved']),
                                  cancel_url=f"{public_site_url()}/#/reserva?id={b['id']}&pago=cancelado")


def start_experience_checkout(db, user, eb):
    """Experiences are booked on request; once confirmed by the organiser they are paid online when it charges online.
    The price is per person (price × participants). Centres and freelance professionals alike."""
    if eb['status'] not in ('confirmed', 'accepted_pending_payment'): raise ValueError('El organizador todavía no ha aceptado tu solicitud.')
    if (eb['payment_status'] if 'payment_status' in eb.keys() else None) == 'paid': raise ValueError('Esta experiencia ya está pagada.')
    e = db.execute('SELECT * FROM travel_experiences WHERE id=?', (eb['travel_experience_id'],)).fetchone()
    if not e: raise ValueError('Experiencia no disponible.')
    reuse = _open_order(db, 'experience_booking_id=?', (eb['id'],))
    if reuse: return {'checkout_url': reuse['checkout_url'], 'order_id': reuse['id'], 'reused': True}
    payee = payee_of(db, e['center_id'], e['provider_user_id'])
    if not payee or not payee_ready(payee): raise ValueError('Este organizador no cobra online: pagarás directamente con él.')
    amount = round(float(e['price'] or 0) * max(1, int(eb['participants'] or 1)), 2)
    return create_stripe_checkout(db, user, amount=amount, currency=e['currency'] or 'EUR', title=e['title'], payee=payee,
                                  provider_user_id=e['provider_user_id'], experience_booking_id=eb['id'], cancel_url=f'{public_site_url()}/#/area?payment=cancelled')


def warn_payment_mode_without_payments(db, center_id=None, user_id=None):
    """A provider lost its online payments: its «Pago al reservar» services stop being bookable (never silently
    «pay at the centre») and it is told to move them to «Bajo petición». Centres, or freelance without a centre."""
    if center_id:
        svcs = db.execute("SELECT id,title FROM provider_services WHERE center_id=? AND active=1 AND booking_mode='payment'", (center_id,)).fetchall()
        row = db.execute('SELECT payments_warning_at FROM centers WHERE id=?', (center_id,)).fetchone(); table, key = 'centers', center_id
    else:
        svcs = db.execute("SELECT id,title FROM provider_services WHERE provider_user_id=? AND center_id IS NULL AND active=1 AND booking_mode='payment'", (user_id,)).fetchall()
        row = db.execute('SELECT payments_warning_at FROM users WHERE id=?', (user_id,)).fetchone(); table, key = 'users', user_id
    if not svcs: return
    if row and row['payments_warning_at'] and row['payments_warning_at'] > (datetime.now(timezone.utc) - _timedelta(days=1)).isoformat(): return
    db.execute(f'UPDATE {table} SET payments_warning_at=? WHERE id=?', (now(), key))
    names = ', '.join(s['title'] for s in svcs)
    for email, name, lang in provider_recipients(db, center_id, user_id):
        queue_email(db, 'center_payments_disabled', email, name, {'services': names, 'panel_url': f'{public_site_url()}/#/admin?tab=services'}, lang, ('center', center_id) if center_id else ('user', user_id))


def new_password_reset(db, user_id):
    token = secrets.token_urlsafe(32)
    exp = (datetime.now(timezone.utc) + _timedelta(hours=1)).isoformat(timespec='seconds')
    db.execute('UPDATE password_resets SET used_at=? WHERE user_id=? AND used_at IS NULL', (now(), user_id))
    db.execute('INSERT INTO password_resets(token_hash,user_id,expires_at,created_at) VALUES(?,?,?,?)', (hashlib.sha256(token.encode()).hexdigest(), user_id, exp, now()))
    return token


def export_user_data(db, uid):
    """Right of access / portability: every row about the user, as JSON (secrets left out)."""
    out = {'exported_at': now(), 'site': public_site_url()}
    u = db.execute('SELECT id,fullname,email,username,role,created_at,last_login,provider_bio,avatar_url,instagram_url,facebook_url,twitter_url,youtube_url,tiktok_url,terms_version,terms_accepted_at FROM users WHERE id=?', (uid,)).fetchone()
    out['account'] = dict(u) if u else {}
    skip = {'sessions', 'password_resets', 'email_outbox', 'audit_log', 'login_attempts'}
    for t in [r['name'] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()]:
        if t in skip or t == 'users' or t.startswith('sqlite_'): continue
        cols = [r['name'] for r in db.execute(f'PRAGMA table_info("{t}")').fetchall()]
        if 'user_id' not in cols: continue
        keep = [c for c in cols if c not in ('password_hash', 'token_hash', 'api_key_hash', 'file_path', 'internal_notes')]
        rows = db.execute(f'SELECT {",".join(chr(34) + c + chr(34) for c in keep)} FROM "{t}" WHERE user_id=? LIMIT 5000', (uid,)).fetchall()
        if rows: out[t] = [dict(r) for r in rows]
    out['messages_received'] = [dict(r) for r in db.execute('SELECT subject,body,created_at,read_at FROM messages WHERE recipient_user_id=? ORDER BY id DESC LIMIT 2000', (uid,)).fetchall()]
    out['emails_sent_to_you'] = [dict(r) for r in db.execute('SELECT template,subject,status,created_at,sent_at FROM email_outbox WHERE to_email=(SELECT lower(email) FROM users WHERE id=?) ORDER BY id DESC LIMIT 500', (uid,)).fetchall()]
    return out


def delete_user_account(db, user):
    """Right to erasure: personal data removed or anonymised. Bookings and payments stay (anonymised) for the centres' and
    the tax obligations; reviews stay without the author's name."""
    uid = user['id']
    future = db.execute("SELECT COUNT(*) FROM bookings WHERE user_id=? AND status IN ('pending','confirmed') AND booking_date>=?", (uid, _dt.date.today().isoformat())).fetchone()[0]
    if future: raise ValueError(f'Tienes {future} reserva(s) próxima(s). Cancélalas antes de eliminar tu cuenta.')
    notify_user(db, uid, 'account_deleted', related=('user', uid))
    for d in db.execute('SELECT file_path FROM user_documents WHERE user_id=?', (uid,)).fetchall():
        delete_document_file(d['file_path'])
    tag = secrets.token_hex(4)
    db.execute('''UPDATE users SET fullname='Usuario eliminado', email=?, username=?, password_hash='!', provider_bio=NULL, avatar_url=NULL,
                  instagram_url=NULL, facebook_url=NULL, twitter_url=NULL, youtube_url=NULL, tiktok_url=NULL WHERE id=?''',
               (f'eliminado-{uid}-{tag}@sin-email.worldives.local', f'eliminado_{uid}_{tag}', uid))
    db.execute('DELETE FROM user_profiles WHERE user_id=?', (uid,))
    for sql in ('DELETE FROM user_documents WHERE user_id=?', 'DELETE FROM sessions WHERE user_id=?', 'DELETE FROM logbook_entries WHERE user_id=?',
                'DELETE FROM center_links WHERE user_id=?', 'DELETE FROM password_resets WHERE user_id=?', 'DELETE FROM messages WHERE recipient_user_id=?',
                "UPDATE promotion_codes SET status='revoked',revoked_at=? WHERE user_id=? AND status='active'",
                'UPDATE bookings SET contact_phone=NULL, notes=NULL, equipment_notes=NULL, guide_notes=NULL WHERE user_id=?'):
        db.execute(sql, (now(), uid) if sql.count('?') == 2 else (uid,))
    audit(db, uid, 'account_deleted', 'user', uid)


REPORT_REASONS = {'illegal': 'Contenido ilegal', 'false': 'Información falsa o engañosa', 'fake_review': 'Reseña falsa o no auténtica',
                  'ip': 'Uso no autorizado de fotos o textos', 'safety': 'Riesgo para la seguridad', 'privacy': 'Datos personales publicados sin permiso',
                  'fraud': 'Fraude o estafa', 'other': 'Otro motivo'}
REPORT_LIMIT = {}


def report_rate_limited(ip):
    current = time.time(); row = REPORT_LIMIT.get(ip)
    if not row or current - row[0] > 3600: REPORT_LIMIT[ip] = [current, 1]; return False
    row[1] += 1
    return row[1] > 10


def _qr_cmds(payload,x0,y0,size):
    import qrcode
    qr=qrcode.QRCode(box_size=1,border=1); qr.add_data(payload); qr.make(fit=True); m=qr.get_matrix(); n=len(m); c=size/n
    a=['q','1 1 1 rg',f'{x0-8:.2f} {y0-8:.2f} {size+16:.2f} {size+16:.2f} re f','0 0 0 rg']
    for r,row in enumerate(m):
        for col,v in enumerate(row):
            if v:a.append(f'{x0+col*c:.2f} {y0+(n-1-r)*c:.2f} {c+.03:.2f} {c+.03:.2f} re f')
    a.append('Q'); return a

ES_MONTHS = ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre']
ES_DAYS = ['lunes','martes','miércoles','jueves','viernes','sábado','domingo']


def es_long_date(value):
    try:
        d=_dt.date.fromisoformat(str(value)[:10]); return f'{ES_DAYS[d.weekday()]}, {d.day} de {ES_MONTHS[d.month-1]} de {d.year}'
    except Exception: return str(value or '')


def booking_pdf(db, booking_id, base_url='http://localhost:8000', lang='es'):
    """«Justificante de reserva» (Fase 2.8): everything the diver needs at the dive centre, even without internet,
    who provides the service (with its fiscal data) and that WORLDIVES DISCOVERY is only the booking platform.
    It is not an invoice. Any of the 10 languages prints correctly (fonts embedded, wod.pdf)."""
    b = db.execute("""SELECT b.*,u.fullname,u.email,up.phone AS customer_phone,p.name AS point_name,s.title AS service_title,s.duration_minutes
                        FROM bookings b JOIN users u ON u.id=b.user_id LEFT JOIN user_profiles up ON up.user_id=u.id
                        LEFT JOIN dive_points p ON p.id=b.dive_point_id LEFT JOIN provider_services s ON s.id=b.service_id WHERE b.id=?""", (booking_id,)).fetchone()
    if not b: return None
    lang = lang if lang in MAIL_LANGS else 'es'
    t = lambda s, **kw: mail_t(lang, s, **kw)
    _svc, prov = booking_payee(db, b); prov = prov or {'type': 'center', 'name': '—'}
    po = db.execute("SELECT id,paid_at,card_brand,card_last4,amount_received,payment_kind FROM payment_orders WHERE booking_id=? AND status IN ('paid','partially_refunded','refunded') ORDER BY id DESC LIMIT 1", (booking_id,)).fetchone()
    DEEP = (0.027, 0.212, 0.290); SEA = (0.043, 0.478, 0.537); MUTED = (0.38, 0.43, 0.46); LINE = (0.86, 0.89, 0.91); SOFT = (0.955, 0.972, 0.978); WHITE = (1, 1, 1); INK = (0.07, 0.13, 0.16)
    WARN = (0.66, 0.42, 0.07); BAD = (0.61, 0.25, 0.22); GOOD = (0.184, 0.478, 0.388)
    tone = {'confirmed': GOOD, 'completed': SEA, 'requested': WARN, 'accepted_pending_payment': WARN, 'payment_in_progress': WARN, 'expired': MUTED, 'rejected': BAD, 'cancelled': BAD}
    state = wbk.normalize_state(b['status'])
    PAY = {'paid': ('Pagado', GOOD), 'deposit_paid': ('Señal pagada', GOOD), 'required': ('Pago pendiente', WARN), 'pending': ('Pago en curso', WARN),
           'at_center': ('Pago en el centro', SEA), 'not_required': ('Sin cobro', SEA), 'review': ('Pago en revisión', WARN), 'refunded': ('Devuelto', MUTED),
           'partially_refunded': ('Devolución parcial', MUTED), 'not_paid': ('No pagado', MUTED)}
    cur = (b['currency'] or 'EUR').upper()
    money = lambda v: mail_money(v, cur, lang)
    ref = f'WOD-{int(booking_id):06d}'
    pg = wpdf.Document(t('Justificante de reserva') + ' ' + ref, lang); W = 595
    # Header
    pg.rect(0, 742, W, 100, DEEP); pg.rect(0, 738, W, 4, SEA)
    pg.text(40, 800, 'WORLDIVES DISCOVERY', 17, WHITE, True)
    pg.text(40, 781, t('Justificante de reserva'), 11, (0.78, 0.88, 0.91), True)
    pg.text(555, 806, t('Nº de reserva').upper(), 7, (0.70, 0.82, 0.86), align='right')
    pg.text(555, 786, ref, 17, WHITE, True, align='right')
    pg.text(555, 768, t('Emitido: {when}', when=_dt.datetime.now().strftime('%d/%m/%Y %H:%M')), 7.5, (0.70, 0.82, 0.86), align='right')
    # Status pills
    y = 708; x = 40
    for label, col in ((t(wbk.state_label(state)), tone.get(state, MUTED)), (t(PAY.get(b['payment_status'], (b['payment_status'] or '', MUTED))[0]), PAY.get(b['payment_status'], ('', MUTED))[1])):
        if not label: continue
        w = pg.width(label.upper(), 8, True) + 26
        pg.box(x, y - 6, w, 22, col, None, 11); pg.text(x + 13, y + 1.5, label.upper(), 8, WHITE, True); x += w + 8
    # Title
    pg.text(40, 674, pg.fit(b['service_title'] or t('Inmersión'), 22, 515, True), 22, INK, True)
    pg.text(40, 655, pg.fit(t('Prestado por {provider}', provider=prov['name']) + (f" · {prov.get('city')}" if prov.get('city') else ''), 12, 515), 12, SEA, True)
    when = mail_date(b['booking_date'], lang) + ' · ' + (b['booking_time'] or t('hora por confirmar'))
    pg.text(40, 637, when[:1].upper() + when[1:], 10.5, MUTED)
    # Details card + QR
    top = 618; pg.box(40, top - 214, 350, 214, WHITE, LINE, 12); pg.box(402, top - 214, 153, 214, SOFT, None, 12)
    pg.text(56, top - 22, t('Detalles').upper(), 7.5, MUTED, True)
    eq = b['equipment_items'] or (t('Sí') if b['needs_equipment'] else t('Equipo propio'))
    rows = [(t('Fecha'), '/'.join(reversed(str(b['booking_date'] or '').split('-'))) or '—'), (t('Hora'), b['booking_time'] or t('Por confirmar')),
            (t('Punto de buceo'), b['point_name'] or t('A concretar con el centro')), (t('Buceadores'), str(b['participants'] or 1)),
            (t('Titular'), (b['contact_name'] if is_guest_user(db, b['user_id']) and b['contact_name'] else b['fullname']) or '—'), (t('Contacto'), b['customer_phone'] or b['contact_phone'] or '—'),
            (t('Equipo de alquiler'), eq), (t('Extras'), ', '.join(t(x) for x, on in (('Guía', b['needs_guide']), ('Nitrox', b['nitrox']), ('Traslado', b['pickup'])) if on) or t('Ninguno'))]
    for i, (lab, val) in enumerate(rows):
        cx = 56 + (i % 2) * 168; cy = top - 44 - (i // 2) * 42
        pg.text(cx, cy, lab.upper(), 6.5, MUTED, True)
        for j, ln in enumerate(pg.wrap(val, 9.5, 152, True, 2)): pg.text(cx, cy - 13 - j * 11, ln, 9.5, INK, True)
    qr = booking_check_url(db, booking_id, base_url)
    try: pg.c += _qr_cmds(qr, 421, top - 140, 115)
    except Exception: pg.box(421, top - 140, 115, 115, WHITE, LINE, 6)
    pg.text(478, top - 18, t('Verificar').upper(), 7.5, MUTED, True, align='center')
    pg.text(478, top - 162, pg.fit(t('Muestra este QR en el centro'), 7.5, 140, True), 7.5, INK, True, align='center')
    pg.text(478, top - 182, ref, 10, DEEP, True, align='center')
    pg.text(478, top - 196, t('Válido sin conexión'), 6.5, MUTED, align='center')
    # Amount and payment
    y0 = top - 230; lines = []
    try: lines = json.loads(b['price_breakdown'] or '[]') or []
    except Exception: lines = []
    if not lines: lines = [{'label': b['service_title'] or t('Actividad'), 'qty': b['participants'] or 1, 'unit': float(b['price'] or 0) / max(1, int(b['participants'] or 1)), 'total': float(b['price'] or 0)}]
    lines = lines[:6]
    paid = float(b['amount_paid'] or 0); refunded = float(b['refunded_total'] or 0); due = float(b['amount_due'] if b['amount_due'] is not None else max(0.0, float(b['price'] or 0) - paid))
    extra_rows = []
    if paid > 0:
        how = f"{(po['card_brand'] or '').title()} ···· {po['card_last4']}" if po and po['card_last4'] else (b['payment_method'] or '')
        extra_rows.append((t('Señal pagada') if b['payment_status'] == 'deposit_paid' else t('Pagado'), money(paid), how))
    if due > 0.005 and state not in ('cancelled', 'rejected', 'expired'):
        extra_rows.append((t('Pendiente de pago en el centro') if b['payment_status'] in ('deposit_paid', 'at_center') else t('Pendiente de pago'), money(due), ''))
    if refunded > 0: extra_rows.append((t('Devuelto'), money(refunded), ''))
    h = 92 + len(lines) * 18 + len(extra_rows) * 16
    pg.box(40, y0 - h, 515, h, WHITE, LINE, 12)
    pg.text(56, y0 - 22, t('Importe y pago').upper(), 7.5, MUTED, True)
    yy = y0 - 42
    for l in lines:
        pg.text(56, yy, pg.fit(l.get('label') or '', 9.5, 300), 9.5, INK)
        pg.text(400, yy, f"{l.get('qty') or 1} × {money(l.get('unit'))}", 8.5, MUTED, align='right')
        pg.text(539, yy, money(l.get('total')), 9.5, INK, align='right'); yy -= 18
    pg.line(56, yy + 8, 539, yy + 8)
    pg.text(56, yy - 8, t('Total'), 11, INK, True); pg.text(539, yy - 8, money(b['price']), 13, INK, True, align='right')
    pg.text(56, yy - 22, t('Precio final fijado por el centro, impuestos incluidos.'), 7.5, MUTED)
    yy -= 40
    for lab, val, how in extra_rows:
        pg.text(56, yy, lab, 9, INK, True); pg.text(539, yy, val, 9, INK, True, align='right')
        if how: pg.text(300, yy, pg.fit(how, 8, 140), 8, MUTED, align='right')
        yy -= 16
    # Provider + platform + policy
    y1 = y0 - h - 14; hb = 170
    pg.box(40, y1 - hb, 250, hb, SOFT, None, 12); pg.box(302, y1 - hb, 253, hb, SOFT, None, 12)
    pg.text(56, y1 - 20, t('Prestador del servicio').upper(), 7.5, MUTED, True)
    pg.text(56, y1 - 37, pg.fit(prov.get('legal_name') or prov['name'], 11, 220, True), 11, INK, True)
    cy = y1 - 53
    addr = prov.get('fiscal_address') or ', '.join(x for x in (prov.get('address'), prov.get('city'), prov.get('country')) if x)
    for lab, val in ((t('NIF'), prov.get('tax_id') or t('pendiente de completar por el prestador')), (t('Dirección'), addr), (t('Teléfono'), prov.get('phone')), (t('Email'), prov.get('email'))):
        if not val: continue
        wl = pg.wrap(val, 8.5, 150, False, 2)
        pg.text(56, cy, lab, 7, MUTED, True)
        for j, ln in enumerate(wl): pg.text(122, cy - j * 10.5, ln, 8.5, INK)
        cy -= 12 + 10.5 * (len(wl) - 1)
    legal = legal_settings(db)
    plat = ' · '.join(x for x in (legal.get('owner_name'), legal.get('nif')) if x)
    pg.text(56, y1 - hb + 26, pg.fit(t('WORLDIVES DISCOVERY: plataforma de reservas.'), 7.5, 220, True), 7.5, SEA, True)
    if plat: pg.text(56, y1 - hb + 14, pg.fit(plat, 7, 220), 7, MUTED)
    pg.text(318, y1 - 20, t('Política de cancelación').upper(), 7.5, MUTED, True)
    pol = booking_policy(db, b, lang)
    ty = y1 - 38
    for ln in pg.wrap(pol['text'], 8.5, 222, False, 4): pg.text(318, ty, ln, 8.5, INK); ty -= 11
    if pol['note']:
        for ln in pg.wrap(pol['note'], 7.5, 222, False, 2): pg.text(318, ty, ln, 7.5, MUTED); ty -= 10
    ty -= 8
    pg.text(318, ty, t('Antes de bucear').upper(), 7.5, MUTED, True); ty -= 16
    for tip in (t('Llega 15–20 minutos antes de la hora.'), t('Lleva tu titulación y el seguro de buceo.'), t('Documento de identidad o pasaporte.')):
        pg.check(318, ty - 1, GOOD); pg.text(332, ty, pg.fit(tip, 8, 210), 8, INK); ty -= 14
    # Footer
    pg.line(40, 62, 555, 62)
    pg.text(40, 46, pg.fit(t('Este documento no es una factura.') + ' ' + t('Escanea el QR para comprobar el estado actualizado de la reserva.'), 7, 515), 7, MUTED)
    pg.text(40, 35, t('El QR no contiene datos personales.'), 7, MUTED)
    pg.text(555, 35, base_url.replace('https://', '').replace('http://', '').rstrip('/'), 7, SEA, True, align='right')
    return pg.pdf()


def diver_sheet_pdf(db,booking_id,base_url="http://localhost:8000",lang="es"):
    b=db.execute("""SELECT b.*,u.fullname,u.email,up.phone AS customer_phone,up.city,up.emergency_contact_name,up.emergency_contact_phone,up.equipment_required,up.suit_type,up.suit_size,up.boot_size,up.bcd_size,up.fin_size,up.mask_size,up.usual_weight_kg,up.tank_preference,up.computer_preference,c.name AS certification_name,COALESCE(ce.name,pu.fullname) AS center_name,p.name AS point_name,s.title AS service_title FROM bookings b JOIN users u ON u.id=b.user_id LEFT JOIN user_profiles up ON up.user_id=u.id LEFT JOIN certifications c ON c.id=up.certification_id LEFT JOIN centers ce ON ce.id=b.center_id LEFT JOIN users pu ON pu.id=b.provider_user_id LEFT JOIN dive_points p ON p.id=b.dive_point_id LEFT JOIN provider_services s ON s.id=b.service_id WHERE b.id=?""",(booking_id,)).fetchone()
    if not b:return None
    qr=booking_check_url(db,booking_id,base_url)
    d=wpdf.Document('Ficha del buceador',lang)
    col=lambda c:tuple(float(x) for x in c.split()) if c else None
    box=lambda x,y,w,h,fill='1 1 1',stroke=None,r=10:d.box(x,y,w,h,col(fill),col(stroke),r)
    text=lambda x,y,s,size=10,color='0.04 0.17 0.24':d.text(x,y,s,size,col(color))
    def lv(x,y,label,value): text(x,y,label.upper(),7,'0.38 0.43 0.46'); text(x,y-13,d.fit(value,9,145),9,'0.04 0.17 0.24')
    box(24,24,547,794,'1 1 1','0.86 0.89 0.91',16)
    box(24,748,547,70,'0.04 0.17 0.24',None,16)
    text(46,790,'WORLDIVES DISCOVERY',21,'1 1 1')
    text(46,773,'FICHA OPERATIVA DEL CENTRO',8,'0.78 0.88 0.91')
    text(46,725,'FICHA DEL BUCEADOR',17,'0.04 0.17 0.24')
    text(46,705,b['fullname'],10,'0.38 0.43 0.46')
    box(42,610,511,72,'0.94 0.97 0.98',None,10)
    text(58,660,'OPERACIÓN',8,'0.38 0.43 0.46')
    op=[('Centro',b['center_name']),('Fecha',b['booking_date']),('Hora',b['booking_time'] or 'Por confirmar'),('Punto',b['point_name'] or 'A concretar'),('Actividad',b['service_title'] or 'Inmersión'),('Participantes',str(b['participants']))]
    for i,(lab,val) in enumerate(op):
        x=58+(i%3)*165; y=640-(i//3)*30; lv(x,y,lab,str(val))
    box(42,378,330,214,'1 1 1','0.86 0.89 0.91',12)
    text(58,568,'DATOS DEL BUCEADOR',8,'0.38 0.43 0.46')
    diver=[('Nombre',b['fullname']),('Email',b['email'] or '—'),('Teléfono',b['customer_phone'] or '—'),('Ciudad',b['city'] or '—'),('Titulación',b['certification_name'] or 'No indicada'),('Emergencia',' · '.join([x for x in [b['emergency_contact_name'],b['emergency_contact_phone']] if x]) or '—')]
    for i,(lab,val) in enumerate(diver):
        x=58+(i%2)*155; y=540-(i//2)*42; lv(x,y,lab,str(val))
    box(42,180,330,180,'1 1 1','0.86 0.89 0.91',12)
    text(58,336,'EQUIPO Y PREFERENCIAS',8,'0.38 0.43 0.46')
    equip=[('Equipo','Sí' if b['equipment_required'] else 'No'),('Traje / talla',' · '.join([x for x in [b['suit_type'],b['suit_size']] if x]) or '—'),('Botas',b['boot_size'] or '—'),('Chaleco',b['bcd_size'] or '—'),('Aletas',b['fin_size'] or '—'),('Máscara',b['mask_size'] or '—'),('Botella',b['tank_preference'] or '—'),('Ordenador',b['computer_preference'] or '—')]
    for i,(lab,val) in enumerate(equip):
        x=58+(i%2)*155; y=312-(i//2)*35; lv(x,y,lab,str(val))
    box(393,378,160,180,'1 1 1','0.86 0.89 0.91',12)
    text(410,536,'VALIDAR RESERVA',8,'0.38 0.43 0.46')
    d.c += _qr_cmds(qr,416,410,110)
    text(410,395,'Escanea el QR',9,'0.04 0.17 0.24')
    text(410,381,'para comprobar',7,'0.38 0.43 0.46')
    text(410,369,'el estado.',7,'0.38 0.43 0.46')
    box(393,180,160,180,'0.94 0.97 0.98',None,12)
    text(410,336,'RESERVA',8,'0.38 0.43 0.46')
    text(410,312,f'#{booking_id}',13,'0.04 0.17 0.24')
    text(410,285,'Centro',7,'0.38 0.43 0.46')
    text(410,270,str(b['center_name'] or '—')[:20],9,'0.04 0.17 0.24')
    text(410,244,'Uso interno del centro',7,'0.38 0.43 0.46')
    text(42,110,'WORLDIVES DISCOVERY · Ficha operativa de la reserva',7,'0.38 0.43 0.46')
    text(42,91,'El QR sirve para verificar la reserva y no contiene datos personales sensibles.',7,'0.38 0.43 0.46')
    return d.pdf()


from wod import ops as wops

CSP_HEADER = wsec.content_security_policy()
ACCESS_LOG = wops.access_logger(LOG_DIR)


def _alert_errors(events):
    """Repeated 500 errors: one email to the administrators (at most once an hour)."""
    db = connect()
    try:
        notify_admins(db, 'admin_error_alert', {'count': len(events), 'errors': '\n'.join(e[1] for e in events[-10:]), 'site': public_site_url()}, ('system', 0))
        db.commit()
    finally:
        db.close()


ERROR_MONITOR = wops.ErrorMonitor(_alert_errors)


class Handler(BaseHTTPRequestHandler):
    server_version = 'WorldDivesLocal/8.0'
    # A connection that stops sending data is dropped after 30 s instead of holding a worker forever.
    timeout = int(os.environ.get('WOD_SOCKET_TIMEOUT', '30'))

    def log_message(self, fmt, *args):
        # The query string never reaches the logs (it may carry coordinates or searches); the IP is truncated
        # unless WOD_LOG_IP=full, and the access log rotates daily (wod.ops.access_logger, WOD_LOG_RETENTION_DAYS).
        try:
            line = fmt % args
            if '?' in line: line = re.sub(r'\?[^\s"]*', '', line)
            ACCESS_LOG.info('%s - %s', wsec.log_ip(self.client_ip()), line)
        except Exception:
            pass

    def client_ip(self):
        """The visitor's IP. Behind nginx/Caddy it comes from X-Forwarded-For, but only when the TCP peer is one of
        WOD_TRUSTED_PROXIES; otherwise anybody could forge it."""
        ip = getattr(self, '_client_ip', None)
        if ip is None:
            ip = self._client_ip = wsec.client_ip(self.client_address[0], self.headers)
        return ip

    def base_url(self):
        """Absolute base URL for links in QR codes and PDFs: WOD_PUBLIC_URL; Host header only in development."""
        if wcfg.public_url(): return wcfg.public_url()
        host = re.sub(r'[^A-Za-z0-9.:\[\]-]', '', self.headers.get('Host') or f'localhost:{PORT}')
        return f"{wsec.request_scheme(self.client_address[0], self.headers)}://{host}"

    def send_response(self, code, message=None):
        super().send_response(code, message)
        self._sec_sent = False

    def security_headers(self, csp=True):
        self._sec_sent = True
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Referrer-Policy', 'strict-origin-when-cross-origin')
        self.send_header('Permissions-Policy', 'camera=(), microphone=(), geolocation=(self), payment=()')
        self.send_header('Cross-Origin-Opener-Policy', 'same-origin')
        if csp: self.send_header('Content-Security-Policy', CSP_HEADER)
        if wcfg.demo_mode(): self.send_header('X-Robots-Tag', 'noindex, nofollow')
        public_url = os.environ.get('WOD_PUBLIC_URL', '').strip().lower()
        if public_url.startswith('https://'):
            self.send_header('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')

    # Endpoints called by other servers (no browser, no cookie): they authenticate with their own signature or key.
    CSRF_EXEMPT = ('/api/payments/webhook', '/api/payments/webhook/connect', '/api/integrations/bookings')

    def enforce_same_origin(self):
        """G10: every state-changing request from a browser must carry Origin (or Referer) and it must be our origin.
        Requests without both headers are rejected, except the server-to-server endpoints in CSRF_EXEMPT.
        The allowed origin is WOD_PUBLIC_URL (mandatory in production); in development it is the Host header."""
        path = urlparse(self.path).path
        if path in self.CSRF_EXEMPT:
            return
        origin = self.headers.get('Origin') or self.headers.get('Referer')
        if not origin or origin == 'null':
            raise PermissionError('Solicitud bloqueada: falta el origen de la petición.')
        try:
            source = urlparse(origin)
            allowed = os.environ.get('WOD_PUBLIC_URL', '').strip()
            allowed_origins = set()
            if allowed:
                target = urlparse(allowed)
                allowed_origins.add(f'{target.scheme}://{target.netloc}'.lower())
            else:
                host = self.headers.get('Host', '')
                allowed_origins.add(f"{wsec.request_scheme(self.client_address[0], self.headers)}://{host}".lower())
            for extra in wcfg.env('WOD_ALLOWED_ORIGINS').split(','):
                if extra.strip(): allowed_origins.add(extra.strip().rstrip('/').lower())
            source_origin = f'{source.scheme}://{source.netloc}'.lower()
            if source_origin.rstrip('/') not in {a.rstrip('/') for a in allowed_origins}:
                raise PermissionError('Solicitud bloqueada por origen no autorizado.')
        except PermissionError:
            raise
        except Exception:
            raise PermissionError('Solicitud bloqueada por origen no autorizado.')

    def accepts_gzip(self):
        return 'gzip' in (self.headers.get('Accept-Encoding') or '').lower()

    def send_prebuilt_json(self, raw, gz):
        use_gz=self.accepts_gzip(); body=gz if use_gz else raw
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        if use_gz: self.send_header('Content-Encoding', 'gzip')
        self.send_header('Vary', 'Accept-Encoding')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.security_headers()
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, payload, status=200):
        raw = json.dumps(payload, ensure_ascii=False, separators=(',',':')).encode('utf-8')
        gz = len(raw) > 1400 and self.accepts_gzip()
        if gz: raw = gzip_bytes(raw)
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        if gz: self.send_header('Content-Encoding', 'gzip')
        self.send_header('Vary', 'Accept-Encoding')
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.security_headers()
        self.end_headers()
        self.wfile.write(raw)

    def send_file(self, path: Path, content_type=None):
        if not path.exists() or not path.is_file():
            self.send_error(404)
            return
        ct = content_type or mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
        st = path.stat()
        etag = f'"{int(st.st_mtime_ns):x}-{st.st_size:x}"'
        # Images and uploads change name when they change, so browsers may keep them a week;
        # code, styles and the page are revalidated on every visit (cheap 304 thanks to the ETag).
        cache = 'public, max-age=604800' if ct.startswith(('image/','font/')) else 'no-cache'
        if self.headers.get('If-None-Match') == etag:
            self.send_response(304)
            self.send_header('ETag', etag)
            self.send_header('Cache-Control', cache)
            self.security_headers()
            self.end_headers()
            return
        raw = path.read_bytes()
        gz = (ct.startswith(('text/','application/javascript','application/json','application/manifest','image/svg')) and len(raw) > 1400 and self.accepts_gzip())
        if gz:
            key=(str(path),etag)
            cached=_GZIP_CACHE.get(key)
            if cached is None:
                cached=gzip_bytes(raw, 6)
                if len(_GZIP_CACHE) > 64: _GZIP_CACHE.clear()
                _GZIP_CACHE[key]=cached
            raw=cached
        self.send_response(200)
        self.send_header('Content-Type', ct)
        if gz: self.send_header('Content-Encoding', 'gzip')
        self.send_header('Vary', 'Accept-Encoding')
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('ETag', etag)
        self.send_header('Cache-Control', cache)
        self.security_headers()
        self.end_headers()
        self.wfile.write(raw)

    def send_private_file(self, path: Path, download_name: str, inline: bool = True):
        """Private documents (G8): never cached by browsers or proxies, always with Content-Disposition."""
        raw = path.read_bytes()
        ct = wsec.DOCUMENT_TYPES.get(path.suffix.lower(), 'application/octet-stream')
        safe = re.sub(r'[^A-Za-z0-9._-]+', '_', download_name or path.name)[:120] or path.name
        self.send_response(200)
        self.send_header('Content-Type', ct)
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'private, no-store, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Content-Disposition', f"{'inline' if inline else 'attachment'}; filename=\"{safe}\"; filename*=UTF-8''{quote(download_name or path.name)}")
        self.send_header('X-Robots-Tag', 'noindex')
        self.security_headers()
        self.end_headers()
        self.wfile.write(raw)

    def send_bytes(self, raw: bytes, content_type: str, filename: str | None = None, cache: str = 'no-store', inline: bool = False):
        """Generated files (PDF, SVG, CSV, ICS…) with the same security headers as every other answer."""
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', cache)
        if filename:
            safe = re.sub(r'[^A-Za-z0-9._-]+', '_', filename)[:120]
            self.send_header('Content-Disposition', f"{'inline' if inline else 'attachment'}; filename=\"{safe}\"")
        self.security_headers()
        self.end_headers()
        self.wfile.write(raw)

    def redirect(self, location):
        self.send_response(302)
        self.send_header('Location', location)
        self.security_headers()
        self.end_headers()

    def end_headers(self):
        # Any answer that did not add them explicitly (error pages, 30x…) still carries the security headers.
        if not getattr(self, '_sec_sent', True): self.security_headers()
        super().end_headers()
        if self.command == 'HEAD':
            # HEAD (uptime monitors, link checkers): same headers as GET, body discarded.
            self.wfile.flush(); self.wfile = _NullWriter()

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        # Static files are served without touching the database.
        if path.startswith('/assets/uploads/'):
            candidate=(PHOTOS/unquote(path)[len('/assets/uploads/'):]).resolve()
            if not candidate.is_relative_to(PHOTOS.resolve()): self.send_error(403); return
            self.send_file(candidate); return
        if path.startswith('/assets/') or path in PUBLIC_ROOT_FILES:
            candidate=(PUBLIC/unquote(path).lstrip('/')).resolve()
            if not candidate.is_relative_to(PUBLIC.resolve()): self.send_error(403); return
            self.send_file(candidate, PUBLIC_ROOT_FILES.get(path)); return
        with connect() as db:
            try:
                if path.startswith('/storage/'):
                    # Storage is private: documents only through the authenticated API. Images used by the app are public only when deliberately copied to assets.
                    self.send_error(403); return
                if path == '/api/health':
                    # Public health check (uptime monitors): only ok + version (G15). Details: /api/admin/health.
                    db.execute('SELECT 1').fetchone()
                    self.send_json({'ok': True, 'version': APP_VERSION}); return
                if path == '/api/setup/status':
                    # The installation screen only exists while WOD_ALLOW_SETUP=1 and there is no administrator (G9).
                    has_admin = bool(db.execute("SELECT 1 FROM users WHERE role='admin' LIMIT 1").fetchone())
                    self.send_json({'setup_allowed': setup_allowed() and not has_admin, 'configured': has_admin or not setup_allowed(),
                                    'registration_open': registration_open(), 'demo': wcfg.demo_mode(),
                                    'pilot_mode': (db.execute("SELECT value FROM site_settings WHERE key='feature_pilot_mode'").fetchone() or {'value':'0'})['value']=='1'}); return
                if path == '/api/legal/doc':
                    doc=legal_doc(db,clean_text(query.get('slug',[''])[0],40) or '',clean_text(query.get('lang',['es'])[0],5) or 'es')
                    if not doc: self.send_json({'error':'Documento no encontrado'},404); return
                    self.send_json(doc); return
                if path == '/api/legal/info':
                    st=legal_settings(db)
                    self.send_json({'version':LEGAL_VERSION,'docs':LEGAL_DOCS,'owner':{k:st.get(k,'') for k in ('owner_name','trade_name','nif','address','email','phone')},'reasons':REPORT_REASONS}); return
                if path == '/api/account/export':
                    user=require_user(self,db); data=export_user_data(db,user['id']); audit(db,user['id'],'data_exported','user',user['id']); db.commit()
                    raw=json.dumps(data,ensure_ascii=False,indent=2,default=str).encode('utf-8')
                    self.send_response(200); self.send_header('Content-Type','application/json; charset=utf-8')
                    self.send_header('Content-Disposition',f'attachment; filename="worldives-mis-datos-{_dt.date.today().isoformat()}.json"')
                    self.send_header('Content-Length',str(len(raw))); self.send_header('Cache-Control','no-store'); self.security_headers(); self.end_headers(); self.wfile.write(raw); return
                if path == '/api/admin/legal':
                    user=require_user(self,db); require_role(user,{'admin'}); st=legal_settings(db)
                    reports=[dict(r) for r in db.execute('SELECT id,reason,target_url,details,reporter_name,reporter_email,status,resolution,resolved_at,created_at FROM content_reports ORDER BY status=\'open\' DESC, id DESC LIMIT 200').fetchall()]
                    self.send_json({'settings':{k:st.get(k,'') for k in LEGAL_FIELDS},'fields':LEGAL_FIELDS,'docs':LEGAL_DOCS,'version':LEGAL_VERSION,'reports':reports,'reasons':REPORT_REASONS,
                                    'open_reports':sum(1 for r in reports if r['status']=='open')}); return
                if path == '/api/admin/emails':
                    user=require_user(self,db); require_role(user,{'admin'})
                    where=[]; args=[]
                    stf=clean_text(query.get('status',[''])[0],20)
                    if stf: where.append('status=?'); args.append(stf)
                    q=clean_text(query.get('q',[''])[0],80)
                    if q: where.append('(to_email LIKE ? OR subject LIKE ?)'); args += [f'%{q}%',f'%{q}%']
                    tpl=clean_text(query.get('template',[''])[0],40)
                    if tpl: where.append('template=?'); args.append(tpl)
                    page=max(0,int(query.get('page',['0'])[0] or 0))
                    sql_where=(' WHERE '+' AND '.join(where)) if where else ''
                    rows=db.execute(f'SELECT id,template,lang,to_email,to_name,subject,status,related_type,related_id,attempts,last_error,sent_at,created_at FROM email_outbox{sql_where} ORDER BY id DESC LIMIT 50 OFFSET ?',args+[page*50]).fetchall()
                    total=db.execute(f'SELECT COUNT(*) FROM email_outbox{sql_where}',args).fetchone()[0]
                    counts={r['status']:r['n'] for r in db.execute('SELECT status,COUNT(*) AS n FROM email_outbox GROUP BY status').fetchall()}
                    cfg=smtp_config()
                    self.send_json({'items':[dict(r) for r in rows],'total':total,'page':page,'counts':counts,
                                    'smtp':{'enabled':cfg['enabled'],'host':cfg['host'],'port':cfg['port'],'security':cfg['security'],'from':cfg['from'],'from_name':cfg['from_name'],'reply_to':cfg['reply_to'],'user_set':bool(cfg['user'])},
                                    'templates':[{'key':k,'label':EMAIL_TEMPLATE_LABELS.get(k,k),'audience':EMAIL_AUDIENCE[v.get('to','any')]} for k,v in EMAIL_TEMPLATES.items()],
                                    'langs':list(MAIL_LANGS)}); return
                if path.startswith('/api/admin/emails/') and path.rsplit('/',1)[1].isdigit():
                    user=require_user(self,db); require_role(user,{'admin'})
                    r=db.execute('SELECT * FROM email_outbox WHERE id=?',(int(path.rsplit('/',1)[1]),)).fetchone()
                    if not r: self.send_json({'error':'Correo no encontrado'},404); return
                    self.send_json({'item':dict(r)}); return
                if path == '/api/admin/email-preview':
                    user=require_user(self,db); require_role(user,{'admin'})
                    tpl=clean_text(query.get('template',[''])[0],40) or ''; lang=clean_text(query.get('lang',['es'])[0],5) or 'es'
                    if tpl not in EMAIL_TEMPLATES: raise ValueError('Plantilla no válida.')
                    subject,html_doc,text_doc=render_email(db,tpl,lang if lang in MAIL_LANGS else 'es',sample_email_ctx(tpl,lang))
                    self.send_json({'subject':subject,'html':html_doc,'text':text_doc}); return
                if path == '/api/center/promotions':
                    user=require_user(self,db); require_role(user,{'center'})
                    if not user['center_id']: raise ValueError('La cuenta aún no tiene un centro aprobado.')
                    self.send_json(center_promotions(db,user['center_id'])); return
                if path.startswith('/api/center/promotions/') and path.endswith('/codes'):
                    user=require_user(self,db); require_role(user,{'center'}); pid=int(path.split('/')[4])
                    pr=db.execute('SELECT * FROM promotions WHERE id=? AND center_id=?',(pid,user['center_id'])).fetchone()
                    if not pr: self.send_json({'error':'Promoción no encontrada'},404); return
                    rows=db.execute('''SELECT pc.id,pc.code,pc.status,pc.uses,pc.created_at,u.fullname,u.email,
                                              (SELECT MAX(created_at) FROM promotion_redemptions r WHERE r.code_id=pc.id) AS last_used
                                         FROM promotion_codes pc JOIN users u ON u.id=pc.user_id WHERE pc.promotion_id=? ORDER BY pc.id DESC''',(pid,)).fetchall()
                    items=[]
                    for r in rows:
                        d=dict(r); d['state']=promo_state(pr['status'],r['status'],r['uses'],pr['uses_per_code'],pr['valid_from'],pr['valid_until']); items.append(d)
                    self.send_json({'items':items}); return
                if path == '/api/center/partner-search':
                    user=require_user(self,db); require_role(user,{'center'}); q=clean_text(query.get('q',[''])[0],80) or ''
                    if len(q)<2: self.send_json({'items':[]}); return
                    rows=db.execute("SELECT id,name,city,country FROM centers WHERE active=1 AND id<>? AND (name LIKE ? OR city LIKE ?) ORDER BY name LIMIT 12",(user['center_id'] or 0,f'%{q}%',f'%{q}%')).fetchall()
                    self.send_json({'items':[dict(r) for r in rows]}); return
                if path == '/api/my/promotions':
                    user=require_user(self,db)
                    rows=db.execute(PROMO_CODE_SQL.replace('WHERE pc.code=?','WHERE pc.user_id=? ORDER BY pc.id DESC'),(user['id'],)).fetchall()
                    self.send_json({'items':[promo_code_payload(db,r,user) for r in rows]}); return
                if path.startswith('/api/promo/') and path.endswith('/qr.svg'):
                    code=path.split('/')[3].upper()
                    row=db.execute('SELECT 1 FROM promotion_codes WHERE code=?',(code,)).fetchone()
                    if not row: self.send_error(404); return
                    self.send_bytes(qr_svg(f'{self.base_url()}/#/promo/{code}','#07364a'),'image/svg+xml; charset=utf-8',cache='private, max-age=3600'); return
                if path.startswith('/api/promo/'):
                    code=path.split('/')[3].upper(); viewer=current_user(self,db)
                    row=db.execute(PROMO_CODE_SQL,(code,)).fetchone()
                    if not row: self.send_json({'error':'Este código promocional no existe.'},404); return
                    self.send_json(promo_code_payload(db,row,viewer)); return
                if path == '/api/site-media':
                    self.send_json(resolve_site_media(SITE_MEDIA.get(db),query.get('h',['n'])[0],query.get('theme',[None])[0] or None)); return
                if path == '/api/admin/payments':
                    # Fase 2: the administrator sees payments and refunds (money goes straight to each provider) and marks incidents.
                    user=require_user(self,db); require_role(user,{'admin'}); st=clean_text(query.get('status',[''])[0],20) or ''
                    conds=[]; args=[]
                    if st=='incident': conds.append("po.incident IS NOT NULL AND po.incident<>'resolved'")
                    elif st: conds.append('po.status=?'); args.append(st)
                    where=('WHERE '+' AND '.join(conds)) if conds else ''
                    rows=db.execute(f'''SELECT po.id,po.booking_id,po.experience_booking_id,po.amount,po.currency,po.status,po.created_at,po.paid_at,po.amount_received,po.card_brand,po.card_last4,po.receipt_url,
                                               po.charge_type,po.payment_kind,po.refunded_total,po.incident,po.incident_note,po.payee_type,
                                               u.fullname,u.email,COALESCE(c.name,pu.fullname) AS center_name,b.status AS booking_status,b.payment_status AS booking_payment,b.refund_status,b.refund_proposed
                                          FROM payment_orders po JOIN users u ON u.id=po.user_id LEFT JOIN bookings b ON b.id=po.booking_id
                                          LEFT JOIN provider_services s ON s.id=po.service_id LEFT JOIN centers c ON c.id=COALESCE(b.center_id,s.center_id)
                                          LEFT JOIN users pu ON pu.id=COALESCE(b.provider_user_id,po.provider_user_id)
                                          {where} ORDER BY CASE WHEN po.incident IS NOT NULL AND po.incident<>'resolved' THEN 0 WHEN po.status='review' THEN 1 WHEN po.status='pending' THEN 2 ELSE 3 END, po.id DESC LIMIT 400''',args).fetchall()
                    sums={r['status']:{'n':r['n'],'amount':round(r['a'] or 0,2)} for r in db.execute("SELECT status,COUNT(*) n,SUM(COALESCE(amount_received,amount)) a FROM payment_orders GROUP BY status").fetchall()}
                    # «Ingresos» of the providers, by currency (never added across currencies). WORLDIVES takes no commission.
                    income=[dict(r) for r in db.execute("""SELECT UPPER(COALESCE(currency,'EUR')) currency,COUNT(*) n,ROUND(SUM(COALESCE(amount_received,amount)),2) gross,ROUND(SUM(COALESCE(refunded_total,0)),2) refunded
                                                         FROM payment_orders WHERE status IN ('paid','partially_refunded','refunded') GROUP BY 1 ORDER BY 3 DESC""").fetchall()]
                    for r_ in income: r_['net']=round((r_['gross'] or 0)-(r_['refunded'] or 0),2)
                    refunds=[dict(r) for r in db.execute('''SELECT r.id,r.payment_order_id,r.booking_id,r.amount,r.currency,r.reason,r.note,r.status,r.source,r.created_at,COALESCE(c.name,pu.fullname) AS center_name
                                                             FROM payment_refunds r LEFT JOIN bookings b ON b.id=r.booking_id LEFT JOIN centers c ON c.id=b.center_id LEFT JOIN users pu ON pu.id=b.provider_user_id
                                                            ORDER BY r.id DESC LIMIT 200''').fetchall()]
                    proposed=[dict(r) for r in db.execute('''SELECT b.id AS booking_id,b.refund_proposed,b.refund_status,b.refund_proposed_at,b.currency,COALESCE(c.name,pu.fullname) AS center_name
                                                              FROM bookings b LEFT JOIN centers c ON c.id=b.center_id LEFT JOIN users pu ON pu.id=b.provider_user_id
                                                             WHERE b.refund_status IN ('proposed','failed') ORDER BY b.refund_proposed_at LIMIT 200''').fetchall()]
                    self.send_json({'items':[dict(r) for r in rows],'summary':sums,'income':income,'refunds':refunds,'pending_refunds':proposed,'stripe_ready':bool(stripe_secret()),
                                    'webhook_ready':bool(os.environ.get('STRIPE_WEBHOOK_SECRET','').strip()),'connect_webhook_ready':bool(os.environ.get('STRIPE_CONNECT_WEBHOOK_SECRET','').strip())}); return
                if path == '/api/admin/site-themes':
                    user=require_user(self,db); require_role(user,{'admin'}); snap=_build_site_media(db)
                    md=_dt.date.today().strftime('%m-%d')
                    for t in snap['themes']: t['live_north']=theme_is_on(t,md,'north'); t['live_south']=theme_is_on(t,md,'south')
                    cur={'north':(resolve_site_media(snap,'north').get('theme') or {}).get('id'),'south':(resolve_site_media(snap,'south').get('theme') or {}).get('id')}
                    slots=[x for x in site_media_slots() if x['group']=='Portadas de sección']
                    self.send_json({'themes':snap['themes'],'accents':list(THEME_ACCENTS),'slots':slots,'current':cur}); return
                if path == '/api/site-promos':
                    self.send_json(public_promos(db)); return
                if path == '/api/admin/site-promos':
                    user=require_user(self,db); require_role(user,{'admin'})
                    items=[dict(r) for r in db.execute('SELECT * FROM site_promos ORDER BY kind,sort_order,id').fetchall()]
                    for it in items:
                        sp=db.execute("SELECT sponsor_name,sponsor_contact,amount,currency,notes FROM sponsorships WHERE placement=? AND ref_id=? AND ended_at IS NULL ORDER BY id DESC LIMIT 1",('band' if it['kind']=='partner' else 'offer',it['id'])).fetchone()
                        it['sponsor']=dict(sp) if sp else None
                    self.send_json({'items':items,'sponsorships':[dict(r) for r in db.execute('SELECT * FROM sponsorships ORDER BY id DESC LIMIT 300').fetchall()],
                                    'settings':{r['key']:r['value'] for r in db.execute("SELECT key,value FROM site_settings WHERE key LIKE 'partners_%'").fetchall()}}); return
                if path == '/api/center/planning':
                    user=require_user(self,db); require_role(user,{'center','freelance'})
                    self.send_json(center_planning(db,user,query.get('month',[''])[0])); return
                if path == '/api/center/poster-qr':
                    user=require_user(self,db); require_role(user,{'center','freelance'})
                    sid=int(query.get('service',['0'])[0] or 0); slot=int(query.get('slot',['0'])[0] or 0)
                    svc=db.execute('SELECT id,center_id,provider_user_id FROM provider_services WHERE id=?',(sid,)).fetchone() if sid else None
                    if svc and svc['provider_user_id']!=user['id']: raise PermissionError('Ese servicio no pertenece a tu cuenta.')
                    cid=(svc['center_id'] if svc else None) or user['center_id']
                    target=f'#/reservar?center={cid}'+(f'&service={sid}' if svc else '')+(f'&slot={slot}' if svc and slot else '') if cid else (f'#/profesional?id={user["id"]}')
                    url=f'{self.base_url()}/{target}'
                    try: matrix=qr_matrix(url)
                    except ImportError: matrix=None  # the poster is still generated, without the QR code
                    self.send_json({'url':url,'matrix':matrix}); return
                if path == '/api/admin/site-media':
                    user=require_user(self,db); require_role(user,{'admin'})
                    self.send_json({'slots':site_media_slots(),'items':_build_site_media(db)['items']}); return
                if path == '/api/point-directory':
                    self.send_json(point_directory(db, query)); return
                if path == '/api/dive-points/map':
                    self.send_prebuilt_json(*points_map_payload(db)); return
                if path == '/api/travel-directory':
                    self.send_json(travel_directory(db)); return
                if path.startswith('/api/travel-offers/'):
                    tid=int(path.rsplit('/',1)[1])
                    offer=db.execute('SELECT * FROM travel_offers WHERE id=? AND active=1',(tid,)).fetchone()
                    if not offer: self.send_json({'error':'Destino no encontrado'},404); return
                    rows=db.execute('''SELECT e.*, u.fullname AS provider_name, u.role AS provider_role, c.name AS center_name
                                      FROM travel_experiences e LEFT JOIN users u ON u.id=e.provider_user_id LEFT JOIN centers c ON c.id=e.center_id
                                      WHERE e.travel_offer_id=? AND e.active=1 AND e.status='published'
                                        AND (e.service_id IS NULL OR EXISTS(SELECT 1 FROM provider_services ps WHERE ps.id=e.service_id AND ps.active=1)) ORDER BY COALESCE(e.start_date,'9999-12-31'), e.id DESC''',(tid,)).fetchall()
                    self.send_json({'offer':dict(offer),'experiences':enrich_experiences(db,rows)}); return
                if path.startswith('/api/travel-experiences/') and path.rsplit('/',1)[1].isdigit():
                    eid=int(path.rsplit('/',1)[1])
                    row=db.execute('''SELECT e.*, u.fullname AS provider_name, c.name AS center_name, c.logo_url AS center_logo, t.title AS destination_title, t.region AS destination_region
                                      FROM travel_experiences e JOIN travel_offers t ON t.id=e.travel_offer_id LEFT JOIN users u ON u.id=e.provider_user_id LEFT JOIN centers c ON c.id=e.center_id
                                      WHERE e.id=? AND e.active=1 AND e.status='published'
                                        AND (e.service_id IS NULL OR EXISTS(SELECT 1 FROM provider_services ps WHERE ps.id=e.service_id AND ps.active=1))''',(eid,)).fetchone()
                    if not row: self.send_json({'error':'Experiencia no disponible.'},404); return
                    self.send_json({'item':enrich_experiences(db,[row])[0]}); return
                if path == '/api/provider/experiences':
                    user=require_user(self,db); require_role(user,{'center','freelance'})
                    rows=db.execute('''SELECT e.*, t.title AS destination_title, s.title AS service_title,
                                              (SELECT COUNT(*) FROM experience_bookings eb WHERE eb.travel_experience_id=e.id AND eb.status='requested') AS pending_requests
                                         FROM travel_experiences e JOIN travel_offers t ON t.id=e.travel_offer_id LEFT JOIN provider_services s ON s.id=e.service_id
                                        WHERE (e.provider_user_id=? OR (e.center_id IS NOT NULL AND e.center_id=?)) ORDER BY e.active DESC, e.id DESC''',(user['id'],user['center_id'] or -1)).fetchall()
                    reqs=db.execute('''SELECT eb.*, e.title AS experience_title, u.fullname, u.email, up.phone
                                         FROM experience_bookings eb JOIN travel_experiences e ON e.id=eb.travel_experience_id JOIN users u ON u.id=eb.user_id LEFT JOIN user_profiles up ON up.user_id=u.id
                                        WHERE (e.provider_user_id=? OR (e.center_id IS NOT NULL AND e.center_id=?)) ORDER BY CASE eb.status WHEN 'requested' THEN 0 ELSE 1 END, eb.created_at DESC LIMIT 500''',(user['id'],user['center_id'] or -1)).fetchall()
                    offers=db.execute('SELECT id,title,region,kind FROM travel_offers WHERE active=1 ORDER BY title').fetchall()
                    self.send_json({'items':enrich_experiences(db,rows),'requests':[dict(r) for r in reqs],'destinations':[dict(o) for o in offers]}); return
                if path == '/api/my-travel-experiences':
                    user=require_user(self,db)
                    rows=db.execute('''SELECT e.*, t.title AS destination_title, c.name AS center_name FROM travel_experiences e JOIN travel_offers t ON t.id=e.travel_offer_id LEFT JOIN centers c ON c.id=e.center_id WHERE e.provider_user_id=? ORDER BY e.id DESC''',(user['id'],)).fetchall()
                    self.send_json({'items':[dict(r) for r in rows]}); return
                if path == '/api/meta':
                    self.send_json({
                        'countries': [dict(r) for r in db.execute('SELECT id,name FROM countries WHERE active=1 ORDER BY name')],
                        'types': [dict(r) for r in db.execute('SELECT id,name FROM dive_types WHERE active=1 ORDER BY name')],
                        'certifications': [dict(r) for r in db.execute('SELECT id,name FROM certifications WHERE active=1 ORDER BY name')],
                        'zones': [dict(r) for r in db.execute('SELECT id,zone,subregion,country FROM dive_zones WHERE active=1 ORDER BY zone,sort_order,subregion')],
                        'travel': [dict(r) for r in db.execute('SELECT * FROM travel_offers WHERE active=1 ORDER BY title')],
                    })
                    return
                if path == '/api/account/shares':
                    user=require_user(self,db)
                    rows=db.execute('SELECT ds.center_id,ds.source,ds.granted_at,c.name AS center_name,c.city FROM data_shares ds JOIN centers c ON c.id=ds.center_id WHERE ds.user_id=? AND ds.revoked_at IS NULL ORDER BY ds.granted_at DESC',(user['id'],)).fetchall()
                    self.send_json({'items':[dict(r_) for r_ in rows]}); return
                if path == '/api/geocode':
                    # Locality search for «Top 10 cerca de ti». Proxied by our server so the visitor's IP is not sent to a
                    # third party, results are cached and the provider's usage policy (1 request/s, identified client) is respected.
                    q=clean_text(query.get('q',[''])[0],120) or ''
                    if len(q)<2: self.send_json({'items':[]}); return
                    if GEOCODE_LIMIT.hit('geo:'+self.client_ip()): self.send_json({'error':'Demasiadas búsquedas seguidas. Espera un momento.'},429); return
                    self.send_json({'items':geocode_search(q,clean_text(query.get('lang',['es'])[0],5) or 'es')}); return
                if path == '/api/me':
                    user = current_user(self, db)
                    if not user:
                        self.send_json({'authenticated': False})
                    else:
                        profile = db.execute('''SELECT up.*, c.name AS certification_name FROM user_profiles up LEFT JOIN certifications c ON c.id=up.certification_id WHERE up.user_id=?''', (user['id'],)).fetchone()
                        docs = db.execute('SELECT id,document_type,title,expires_at,status,original_name,uploaded_at FROM user_documents WHERE user_id=? ORDER BY expires_at IS NULL, expires_at', (user['id'],)).fetchall()
                        links = db.execute('''SELECT cl.*, c.name AS center_name, c.city, c.country FROM center_links cl JOIN centers c ON c.id=cl.center_id WHERE cl.user_id=? ORDER BY cl.last_checkin DESC''',(user['id'],)).fetchall()
                        claim = db.execute('SELECT status,requested_role,created_at FROM center_claims WHERE user_id=? ORDER BY id DESC LIMIT 1', (user['id'],)).fetchone()
                        self.send_json({'authenticated': True, 'user': public_user(user), 'profile': dict(profile) if profile else None, 'documents': [dict(x) for x in docs], 'center_links':[dict(x) for x in links],
                                        'pro_request': dict(claim) if claim else None})
                    return
                if path.startswith('/api/providers/'):
                    provider_id=int(path.rsplit('/',1)[1])
                    u=db.execute("SELECT id,fullname,role,provider_bio,avatar_url,center_id,instagram_url,facebook_url,twitter_url,youtube_url,tiktok_url FROM users WHERE id=? AND role IN ('center','freelance')",(provider_id,)).fetchone()
                    if not u: self.send_json({'error':'Profesional no encontrado'},404); return
                    result={'id':u['id'],'fullname':u['fullname'],'role':u['role'],'provider_bio':u['provider_bio'] or '', 'avatar_url':u['avatar_url'] or '', 'socials': {k:(u[k] or '') for k in ('instagram_url','facebook_url','twitter_url','youtube_url','tiktok_url')}}
                    if u['role']=='center' and u['center_id']:
                        c=db.execute('SELECT * FROM centers WHERE id=? AND active=1',(u['center_id'],)).fetchone()
                        if c:
                            result['center']=center_row(c)
                    self.send_json(result); return
                if path.startswith('/api/payments/session/'):
                    user=require_user(self,db); sid=path.rsplit('/',1)[1]
                    q='''SELECT po.*,s.title AS service_title,COALESCE(c.name,pu.fullname) AS center_name,b.id AS booking_id,b.status AS booking_status,b.booking_date,b.booking_time,b.participants,b.amount_due,b.deposit_amount
                         FROM payment_orders po LEFT JOIN provider_services s ON s.id=po.service_id LEFT JOIN centers c ON c.id=s.center_id LEFT JOIN users pu ON pu.id=po.provider_user_id LEFT JOIN bookings b ON b.id=po.booking_id
                         WHERE po.provider_payment_id=? AND po.user_id=?'''
                    row=db.execute(q,(sid,user['id'])).fetchone()
                    if not row: self.send_json({'error':'Pago no encontrado'},404); return
                    if row['status']=='pending' and stripe_secret():
                        # Do not wait for the webhook: ask Stripe directly so the diver sees the confirmation at once.
                        try:
                            order=db.execute('SELECT * FROM payment_orders WHERE id=?',(row['id'],)).fetchone()
                            sess=stripe_session(order)
                            ok_,why=finalize_paid_order(db,order,sess,'return'); db.commit()
                            row=db.execute(q,(sid,user['id'])).fetchone()
                        except Exception as exc: sys.stderr.write(f'[pagos] verificación al volver de Stripe: {exc}\n')
                    d=dict(row)
                    for k in ('connected_account_id','checkout_url','platform_fee','provider_payment_id','payment_intent_id','charge_type','payee_type','payee_id','incident','incident_note','incident_at','incident_by','provider_user_id'): d.pop(k,None)
                    d['reference']=f"PAY-{d['id']:05d}"
                    d['booking_ref']=f"WOD-{int(d['booking_id']):06d}" if d.get('booking_id') else ''
                    self.send_json({'payment':d}); return
                if path == '/api/center/analytics':
                    user=require_user(self,db); require_role(user,{'center'}); cid=int(user['center_id'] or 0)
                    if not cid: raise ValueError('La cuenta aún no tiene un centro aprobado.')
                    bookings=db.execute(f'''SELECT b.*,COALESCE(b.contact_name,u.fullname) AS fullname,u.email,s.title AS service_title,p.name AS point_name FROM bookings b JOIN users u ON u.id=b.user_id LEFT JOIN provider_services s ON s.id=b.service_id LEFT JOIN dive_points p ON p.id=b.dive_point_id WHERE b.center_id=? AND b.status NOT IN ('payment_in_progress','expired') ORDER BY b.booking_date,b.booking_time''',(cid,)).fetchall()
                    today=time.strftime('%Y-%m-%d'); total=len(bookings)
                    upcoming=[b for b in bookings if (b['booking_date'] or '')>=today and b['status'] not in ('cancelled','rejected','completed')]
                    # «Ingresos» (never «Facturación»): what clients actually paid, net of refunds, per currency.
                    income={}
                    for b_ in bookings:
                        amt=float(b_['amount_paid'] or 0)-float(b_['refunded_total'] or 0)
                        if amt>0: cur_=(b_['currency'] or 'EUR').upper(); income[cur_]=round(income.get(cur_,0)+amt,2)
                    revenue=max(income.values()) if income else 0.0
                    pending=sum(1 for b in bookings if b['status'] in ('pending','requested')); confirmed=sum(1 for b in bookings if b['status']=='confirmed'); completed=sum(1 for b in bookings if b['status']=='completed'); cancelled=sum(1 for b in bookings if b['status']=='cancelled')
                    participants=sum(int(b['participants'] or 1) for b in bookings if b['status'] not in ('cancelled','rejected'))
                    by_day={}; by_service={}
                    for b in bookings:
                        if b['booking_date']: by_day[b['booking_date']]=by_day.get(b['booking_date'],0)+int(b['participants'] or 1)
                        k=b['service_title'] or 'Reserva manual'; by_service[k]=by_service.get(k,0)+int(b['participants'] or 1)
                    channels={'WORLDIVES':0,'Web del centro':0,'Manual':0}
                    for b in bookings:
                        src=(b['source'] if 'source' in b.keys() else None) or ('web' if (b['external_ref'] or '') else 'online')
                        channels[{'web':'Web del centro','manual':'Manual'}.get(src,'WORLDIVES')]+=1
                    integ=db.execute('SELECT enabled,api_key_prefix,updated_at FROM center_integrations WHERE center_id=?',(cid,)).fetchone()
                    self.send_json({'metrics':{'total':total,'upcoming':len(upcoming),'pending':pending,'confirmed':confirmed,'completed':completed,'cancelled':cancelled,'revenue':round(revenue,2),'income':[{'currency':k,'amount':v} for k,v in sorted(income.items(),key=lambda x:-x[1])],'participants':participants},'by_day':[{'date':k,'participants':v} for k,v in sorted(by_day.items())[-30:]],'by_service':[{'name':k,'participants':v} for k,v in sorted(by_service.items(),key=lambda x:x[1],reverse=True)[:8]],'channels':channels,'integration':dict(integ) if integ else {'enabled':False}}); return
                if path == '/api/center/integration':
                    user=require_user(self,db); require_role(user,{'center'}); cid=int(user['center_id'] or 0)
                    row=db.execute('SELECT enabled,api_key_prefix,updated_at,created_at FROM center_integrations WHERE center_id=?',(cid,)).fetchone()
                    self.send_json({'configured':bool(row),'integration':dict(row) if row else None}); return
                if path == '/api/provider-services':
                    provider_id=int(query.get('provider_id',['0'])[0] or 0)
                    # Paused services are only listed for their own provider (management panel). Public listings stay active-only.
                    include_inactive=0
                    center_filter=int(query.get('center_id',['0'])[0] or 0)  # booking engine asks only for one center's catalog
                    if provider_id and query.get('include_inactive',['0'])[0]=='1':
                        viewer=current_user(self,db)
                        include_inactive=1 if viewer and int(viewer['id'])==provider_id else 0
                    if not provider_id and not center_filter:
                        # Never dump the whole marketplace catalog in one answer: ask for one center or provider.
                        raise ValueError('Indica el centro o el profesional cuyo catálogo quieres ver.')
                    rows=db.execute('''SELECT s.*, u.fullname AS provider_name, c.name AS center_name
                                      FROM provider_services s JOIN users u ON u.id=s.provider_user_id
                                      LEFT JOIN centers c ON c.id=s.center_id
                                      WHERE (s.active=1 OR ?=1) AND (?=0 OR s.provider_user_id=?) AND (?=0 OR s.center_id=?) ORDER BY s.title''',(include_inactive,provider_id,provider_id,center_filter,center_filter)).fetchall()
                    result=[]; ids=[r['id'] for r in rows]
                    slots_by_service={}; points_by_slot={}; exp_by_service={}
                    # Batched queries: a constant number of queries per request instead of one per departure.
                    for chunk in [ids[i:i+500] for i in range(0,len(ids),500)]:
                        marks=','.join('?'*len(chunk))
                        for x in db.execute(f"""SELECT * FROM (SELECT ss.*, ROW_NUMBER() OVER (PARTITION BY service_id ORDER BY slot_date,slot_time) AS rn FROM service_slots ss
                                                 WHERE service_id IN ({marks}) AND status IN ('open','full') AND (slot_date > date('now') OR (slot_date=date('now') AND slot_time>=time('now'))))
                                                WHERE rn<=100 ORDER BY service_id,slot_date,slot_time""",chunk).fetchall():
                            sd=dict(x); sd.pop('rn',None); sd['points']=[]; slots_by_service.setdefault(x['service_id'],[]).append(sd)
                        if include_inactive:
                            for ex in db.execute(f'SELECT id,service_id,travel_offer_id,status,active FROM travel_experiences WHERE service_id IN ({marks})',chunk).fetchall():
                                exp_by_service[ex['service_id']]=dict(ex)
                    slot_ids=[sd['id'] for lst in slots_by_service.values() for sd in lst]
                    for chunk in [slot_ids[i:i+500] for i in range(0,len(slot_ids),500)]:
                        for pp in db.execute(f"SELECT sp.slot_id,p.id,p.name,p.country,p.region FROM service_slot_points sp JOIN dive_points p ON p.id=sp.dive_point_id WHERE sp.slot_id IN ({','.join('?'*len(chunk))}) AND p.active=1 ORDER BY p.name",chunk).fetchall():
                            points_by_slot.setdefault(pp['slot_id'],[]).append({'id':pp['id'],'name':pp['name'],'country':pp['country'],'region':pp['region']})
                    ready_cache={}; payee_cache={}
                    for r in rows:
                        d=dict(r)
                        tariff_price, tariff_currency, tariff_effective = effective_service_tariff(db, r['id'])
                        d['price']=tariff_price; d['currency']=tariff_currency; d['tariff_effective_from']=tariff_effective
                        rk=(r['center_id'],r['provider_user_id'] if not r['center_id'] else None)
                        if rk not in ready_cache: ready_cache[rk]=service_payments_ready(db,r)
                        d.update(service_mode_info(db,r,tariff_price,ready_cache[rk]))
                        if rk not in payee_cache: payee_cache[rk]=payee_of(db,r['center_id'],r['provider_user_id'])
                        pol_=provider_policy(payee_cache[rk],r); d['policy']={'free_hours':pol_['free_hours'],'refund_pct':pol_['refund_pct'],'text':pol_['text'],'note':pol_['note'],'own':r['cancel_free_hours'] is not None}
                        d['provider_name']=(payee_cache[rk] or {}).get('name') or d.get('center_name') or d.get('provider_name')
                        if include_inactive: d['experience']=exp_by_service.get(r['id'])
                        d['slots']=slots_by_service.get(r['id'],[])
                        for sd in d['slots']: sd['points']=points_by_slot.get(sd['id'],[])
                        result.append(d)
                    self.send_json({'items':result}); return
                if path.startswith('/api/provider-services/'):
                    sid=int(path.rsplit('/',1)[1]); r=db.execute('''SELECT s.*,u.fullname AS provider_name,c.name AS center_name,c.phone AS center_phone,c.email AS center_email
                                                                    FROM provider_services s JOIN users u ON u.id=s.provider_user_id LEFT JOIN centers c ON c.id=s.center_id
                                                                    WHERE s.id=? AND s.active=1''',(sid,)).fetchone()
                    if not r: self.send_json({'error':'Servicio no encontrado'},404); return
                    rd=dict(r); tariff_price, tariff_currency, tariff_effective=effective_service_tariff(db, sid)
                    rd['price']=tariff_price; rd['currency']=tariff_currency; rd['tariff_effective_from']=tariff_effective
                    rd.update(service_mode_info(db,r,tariff_price))
                    _pol=provider_policy(payee_of(db,r['center_id'],r['provider_user_id']),r); rd['policy']={'free_hours':_pol['free_hours'],'refund_pct':_pol['refund_pct'],'text':_pol['text'],'note':_pol['note']}
                    slots=db.execute("SELECT * FROM service_slots WHERE service_id=? AND status IN ('open','full','closed') ORDER BY slot_date,slot_time",(sid,)).fetchall()
                    slot_out=[]
                    for x in slots:
                        sd=dict(x); sd['points']=[dict(pp) for pp in db.execute('SELECT p.id,p.name,p.country,p.region FROM service_slot_points sp JOIN dive_points p ON p.id=sp.dive_point_id WHERE sp.slot_id=? AND p.active=1 ORDER BY p.name',(x['id'],)).fetchall()]; slot_out.append(sd)
                    self.send_json({'service':rd,'slots':slot_out}); return
                if path == '/api/center/tariffs':
                    user=require_user(self,db); require_role(user,{'center'}); cid=int(user['center_id'] or 0)
                    services=db.execute('SELECT id,title,service_type,price,currency,color,active FROM provider_services WHERE center_id=? ORDER BY title',(cid,)).fetchall()
                    out=[]
                    for svc in services:
                        hist=db.execute('SELECT id,price,currency,effective_from,active,created_at FROM center_tariffs WHERE center_id=? AND service_id=? ORDER BY effective_from DESC,id DESC',(cid,svc['id'])).fetchall()
                        out.append({'service':dict(svc),'history':[dict(x) for x in hist]})
                    self.send_json({'items':out}); return
                if path in ('/api/payments/center','/api/provider/payments'):
                    # Payments of a provider (centre or freelance without centre): operations, refunds to make and its settings.
                    user=require_user(self,db); require_role(user,{'center','freelance','admin'})
                    payee=self_payee(db,user,{k:v[0] for k,v in query.items()})
                    if payee['type']=='center':
                        where,args='(po.payee_type=\'center\' AND po.payee_id=?) OR po.booking_id IN (SELECT id FROM bookings WHERE center_id=?) OR s.center_id=?',(payee['id'],payee['id'],payee['id'])
                        bk_scope,bk_args='b.center_id=?',[payee['id']]
                    else:
                        where,args='(po.payee_type=\'freelance\' AND po.payee_id=?) OR po.booking_id IN (SELECT id FROM bookings WHERE center_id IS NULL AND provider_user_id=?)',(payee['id'],payee['id'])
                        bk_scope,bk_args='(b.center_id IS NULL AND b.provider_user_id=?)',[payee['id']]
                    rows=db.execute(f'''SELECT po.id,po.booking_id,po.experience_booking_id,po.amount,po.currency,po.status,po.created_at,po.paid_at,po.amount_received,po.refunded_total,
                                              po.payment_kind,po.charge_type,po.card_brand,po.card_last4,po.incident,s.title AS service_title,COALESCE(b.contact_name,u.fullname) AS customer_name
                                         FROM payment_orders po LEFT JOIN provider_services s ON s.id=po.service_id LEFT JOIN bookings b ON b.id=po.booking_id
                                         JOIN users u ON u.id=po.user_id WHERE {where} ORDER BY po.id DESC LIMIT 300''',args).fetchall()
                    income={}
                    for r_ in rows:
                        if r_['status'] in ('paid','partially_refunded','refunded'):
                            cur_=(r_['currency'] or 'EUR').upper(); e_=income.setdefault(cur_,{'currency':cur_,'gross':0.0,'refunded':0.0,'n':0})
                            e_['gross']=round(e_['gross']+float(r_['amount_received'] or r_['amount'] or 0),2); e_['refunded']=round(e_['refunded']+float(r_['refunded_total'] or 0),2); e_['n']+=1
                    for e_ in income.values(): e_['net']=round(e_['gross']-e_['refunded'],2)
                    pending=[dict(r) for r in db.execute(f"""SELECT b.id,b.booking_date,b.booking_time,b.refund_proposed,b.refund_status,b.refund_proposed_at,b.currency,COALESCE(b.contact_name,u.fullname) AS customer_name,s.title AS service_title
                                                             FROM bookings b JOIN users u ON u.id=b.user_id LEFT JOIN provider_services s ON s.id=b.service_id
                                                            WHERE {bk_scope} AND b.refund_status IN ('proposed','failed') ORDER BY b.refund_proposed_at""",bk_args).fetchall()]
                    pol=provider_policy(payee)
                    self.send_json({'items':[dict(x) for x in rows],'income':sorted(income.values(),key=lambda x:-x['net']),'pending_refunds':pending,
                                    'profile':{'type':payee['type'],'name':payee['name'],'legal_name':payee.get('legal_name') or '','tax_id':payee.get('tax_id') or '','fiscal_address':payee.get('fiscal_address') or '',
                                               'cancel_free_hours':pol['free_hours'],'cancel_refund_pct':pol['refund_pct'],'cancellation_note':pol['note'],'policy_text':pol['text']}}); return
                if path=='/api/my/position-suggestions':
                    user=require_user(self,db); require_role(user,{'center','freelance','admin'}); rows=db.execute('''SELECT s.*, p.name AS point_name FROM point_position_suggestions s JOIN dive_points p ON p.id=s.dive_point_id WHERE s.user_id=? ORDER BY s.created_at DESC''',(user['id'],)).fetchall(); self.send_json({'items':[dict(r) for r in rows]}); return
                if path=='/api/admin/travel-experiences':
                    user=require_user(self,db); require_role(user,{'admin'}); rows=db.execute('''SELECT e.*,t.title AS destination_title,u.fullname AS provider_name,c.name AS center_name FROM travel_experiences e JOIN travel_offers t ON t.id=e.travel_offer_id LEFT JOIN users u ON u.id=e.provider_user_id LEFT JOIN centers c ON c.id=e.center_id ORDER BY e.id DESC''').fetchall(); self.send_json({'items':[dict(r) for r in rows]}); return
                if path == '/api/center-extras':
                    # Public: what a diver can add to a booking at this center.
                    cid=int(query.get('center_id',['0'])[0] or 0)
                    rows=db.execute('SELECT id,name,description,price FROM center_extras WHERE center_id=? AND active=1 ORDER BY name',(cid,)).fetchall()
                    self.send_json({'items':[dict(r) for r in rows]}); return
                if path == '/api/booking-quote':
                    cid=int(query.get('center_id',['0'])[0] or 0); sid=int(query.get('service_id',['0'])[0] or 0); slot_id=int(query.get('slot_id',['0'])[0] or 0)
                    if cid: service=db.execute('SELECT * FROM provider_services WHERE id=? AND center_id=? AND active=1',(sid,cid)).fetchone() if sid else None
                    else: service=db.execute('SELECT * FROM provider_services WHERE id=? AND center_id IS NULL AND active=1',(sid,)).fetchone() if sid else None  # freelance
                    slot=db.execute('SELECT slot_date FROM service_slots WHERE id=? AND service_id=?',(slot_id,sid)).fetchone() if slot_id and sid else None
                    pax=max(1,int(query.get('participants',['1'])[0] or 1))
                    total,currency,lines=booking_quote(db,cid or None,service,pax,slot['slot_date'] if slot else None,as_list(query.get('extras',[''])[0]),as_list(query.get('equipment',[''])[0]))
                    dep=deposit_for(service,total,pax)
                    self.send_json({'total':total,'currency':currency,'lines':lines,'deposit':dep,'due_at_center':round(total-dep,2) if dep else 0}); return
                if path == '/api/service-templates':
                    user=require_user(self,db); require_role(user,{'center','freelance'})
                    rows=db.execute('SELECT * FROM service_templates WHERE provider_user_id=? ORDER BY name COLLATE NOCASE',(user['id'],)).fetchall()
                    self.send_json({'items':[dict(r) for r in rows]}); return
                if path == '/api/center/extras':
                    user=require_user(self,db); require_role(user,{'center','admin'})
                    cid=user['center_id'] if user['role']=='center' else int(query.get('center_id',['0'])[0] or 0)
                    rows=db.execute('SELECT * FROM center_extras WHERE center_id=? ORDER BY active DESC,name',(cid,)).fetchall()
                    self.send_json({'items':[dict(r) for r in rows]}); return
                if path == '/api/center-equipment':
                    center_id=int(query.get('center_id',['0'])[0] or 0)
                    defaults=[('fins','Aletas'),('mask','Máscara'),('wetsuit','Traje de neopreno'),('regulator','Regulador'),('bcd','Chaleco BCD'),('tank','Botella'),('computer','Ordenador de buceo'),('full_kit','Equipo completo')]
                    rows=db.execute('SELECT code,label,price,active FROM center_equipment WHERE center_id=? ORDER BY sort_order,label',(center_id,)).fetchall()
                    existing={r['code']:dict(r) for r in rows}
                    items=[existing.get(code,{'code':code,'label':label,'price':None,'active':1}) for code,label in defaults if existing.get(code,{'active':1})['active']]
                    self.send_json({'items':items}); return
                if path == '/api/center-points':
                    # This endpoint is also part of the public booking flow. A recreational
                    # diver or freelance user must be able to see the points that a centre
                    # operates before choosing a date/activity. Centre users are restricted
                    # to their own catalogue; admin can query any centre.
                    user=require_user(self,db); requested_center_id=int(query.get('center_id',['0'])[0] or 0)
                    if user['role']=='center':
                        center_id=int(user['center_id'] or 0)
                    elif user['role']=='admin':
                        center_id=requested_center_id
                    else:
                        center_id=requested_center_id
                    if not center_id: raise ValueError('Centro no válido.')
                    center=db.execute('SELECT id FROM centers WHERE id=? AND active=1',(center_id,)).fetchone()
                    if not center: raise ValueError('Centro no válido.')
                    rows=db.execute('''SELECT p.*, cpl.created_at AS associated_at
                                      FROM center_point_links cpl
                                      JOIN dive_points p ON p.id=cpl.dive_point_id
                                      WHERE cpl.center_id=? AND p.active=1
                                      ORDER BY p.name''',(center_id,)).fetchall()
                    self.send_json({'items':[point_row(r) for r in rows],'center_id':center_id}); return
                if path == '/api/dive-points':
                    q = clean_text(query.get('q',[''])[0], 120)
                    country = clean_text(query.get('country',[''])[0], 120)
                    dtype = clean_text(query.get('type',[''])[0], 120)
                    region = clean_text(query.get('region',[''])[0], 120)
                    zone = clean_text(query.get('zone',[''])[0], 120)
                    subregion = clean_text(query.get('subregion',[''])[0], 120)
                    center_id = query.get('center_id',[''])[0]
                    where = ['p.active=1']
                    args = []
                    if q:
                        like = f'%{fold_text(q)}%'; where.append('(fold(p.name) LIKE ? OR fold(p.country) LIKE ? OR fold(p.region) LIKE ? OR fold(p.subregion) LIKE ? OR fold(p.description) LIKE ?)'); args += [like]*5
                    if country: where.append('p.country=?'); args.append(country)
                    if dtype:
                        # The catalog stores descriptive dive types (e.g. Arrecife, Pared, Pecio,
                        # Muck) while the public "Tipos de buceo" section uses semantic categories.
                        # Keep those categories mutually meaningful instead of doing an exact-string
                        # match that would return the same rows for every button.
                        cat = dive_category(dtype)
                        if cat: where.append(cat['where'])
                        else: where.append('fold(p.dive_type) LIKE ?'); args.append(f'%{fold_text(dtype)}%')
                    if region: where.append('p.region=?'); args.append(region)
                    if zone: where.append('p.zone=?'); args.append(zone)
                    if subregion: where.append('p.subregion=?'); args.append(subregion)
                    if center_id.isdigit(): where.append('p.center_id=?'); args.append(int(center_id))
                    rows = db.execute('''SELECT p.*, c.name AS center_name, rc.name AS recommended_certification_name FROM dive_points p LEFT JOIN centers c ON c.id=p.center_id LEFT JOIN certifications rc ON rc.id=p.recommended_certification_id WHERE '''+' AND '.join(where)+' ORDER BY p.zone,p.subregion,p.country,p.name', args).fetchall()
                    self.send_json({'items':[point_row(r) for r in rows]})
                    return
                if path.startswith('/api/centers/') and path.count('/')==3:
                    cid_txt=path.rsplit('/',1)[1]
                    if cid_txt.isdigit():
                        cid=int(cid_txt)
                        row=db.execute('''SELECT c.*,
                            (SELECT COUNT(*) FROM center_point_links cpl JOIN dive_points dp ON dp.id=cpl.dive_point_id WHERE cpl.center_id=c.id AND dp.active=1) AS point_count,
                            COALESCE((SELECT ROUND(AVG(cr.rating),1) FROM center_reviews cr WHERE cr.center_id=c.id AND cr.active=1),0) AS rating_average,
                            (SELECT COUNT(*) FROM center_reviews cr WHERE cr.center_id=c.id AND cr.active=1) AS review_count
                            FROM centers c WHERE c.id=? AND c.active=1''',(cid,)).fetchone()
                        if not row: self.send_json({'error':'Centro no encontrado'},404); return
                        points=db.execute('SELECT p.* FROM center_point_links cpl JOIN dive_points p ON p.id=cpl.dive_point_id WHERE cpl.center_id=? AND p.active=1 ORDER BY p.name',(cid,)).fetchall()
                        services=db.execute('SELECT s.* FROM provider_services s WHERE s.center_id=? AND s.active=1 ORDER BY s.title',(cid,)).fetchall(); reviews=db.execute('''SELECT cr.id,cr.rating,cr.title,cr.body,cr.verified,cr.created_at,cr.updated_at,u.fullname
                                               FROM center_reviews cr JOIN users u ON u.id=cr.user_id
                                               WHERE cr.center_id=? AND cr.active=1 ORDER BY cr.created_at DESC,cr.id DESC LIMIT 50''',(cid,)).fetchall()
                        review_payload=[dict(r) for r in reviews]
                        current_review=None; can_review=False; review_reason='Podrás dejar una reseña verificada cuando tengas una reserva pagada o confirmada con este centro.'
                        current=current_user(self,db)
                        if current:
                            current_review_row=db.execute('SELECT id,rating,title,body,created_at,updated_at FROM center_reviews WHERE center_id=? AND user_id=? AND active=1',(cid,current['id'])).fetchone()
                            current_review=dict(current_review_row) if current_review_row else None
                            completed_booking=db.execute("SELECT 1 FROM bookings WHERE center_id=? AND user_id=? AND status NOT IN ('cancelled','rejected') AND (payment_status='paid' OR status IN ('confirmed','completed')) LIMIT 1",(cid,current['id'])).fetchone()
                            can_review=bool(completed_booking) and current['role'] not in {'center','admin'}
                            if can_review: review_reason='Puedes valorar tu experiencia. Tu reseña aparece como verificada porque tienes una reserva con este centro.'
                            elif current['role'] in {'center','admin'}: review_reason='Las cuentas profesionales y administrativas no pueden valorar centros.'
                        service_out=[]; c_ready=center_payments_ready(row)
                        for sv in services:
                            sd=dict(sv); sd['price'],sd['currency'],_=effective_service_tariff(db,sv['id'])
                            sd.update(service_mode_info(db,sv,sd['price'],c_ready))
                            sd['next_slots']=[dict(x) for x in db.execute("SELECT id,slot_date,slot_time,spots_available,spots_total FROM service_slots WHERE service_id=? AND status IN ('open','full') AND slot_date>=date('now') ORDER BY slot_date,slot_time LIMIT 3",(sv['id'],)).fetchall()]
                            service_out.append(sd)
                        exp_rows=db.execute('''SELECT e.*, t.title AS destination_title FROM travel_experiences e JOIN travel_offers t ON t.id=e.travel_offer_id
                                               WHERE e.center_id=? AND e.active=1 AND e.status='published'
                                                 AND (e.service_id IS NULL OR EXISTS(SELECT 1 FROM provider_services ps WHERE ps.id=e.service_id AND ps.active=1))
                                               ORDER BY e.id DESC LIMIT 12''',(cid,)).fetchall()
                        _ci=center_row(row); _ci['cancellation_policy']=cancellation_policy_key(row['cancellation_policy']); _ci['cancellation_text']=cancellation_policy_text(row['cancellation_policy']); _ci['cancellation_note']=row['cancellation_note'] or ''
                        self.send_json({'item':_ci,'points':[point_row(r) for r in points],'services':service_out,'experiences':enrich_experiences(db,exp_rows), 'reviews':review_payload, 'review':{'can_review':can_review,'reason':review_reason,'current':current_review}}); return
                if path.startswith('/api/dive-points/') and path.endswith('/virtual'):
                    pid=int(path.split('/')[3])
                    if not db.execute('SELECT 1 FROM dive_points WHERE id=? AND active=1',(pid,)).fetchone():
                        self.send_json({'error':'Punto no encontrado'},404); return
                    rows=db.execute('SELECT id,dive_point_id,title,experience_type,provider,url,media_path,description,duration_seconds,active,created_at,updated_at FROM virtual_experiences WHERE dive_point_id=? AND active=1 ORDER BY id',(pid,)).fetchall()
                    self.send_json({'items':[virtual_public_row(x) for x in rows],'embed_domains':wcfg.embed_domains()}); return
                if path.startswith('/api/dive-points/') and path.endswith('/photos'):
                    user=require_user(self,db); pid=int(path.split('/')[3]); row=db.execute('SELECT center_id FROM dive_points WHERE id=?',(pid,)).fetchone()
                    if not row: self.send_error(404); return
                    if user['role']=='center' and row['center_id']!=user['center_id']: raise PermissionError('No puedes modificar las fotos de este punto.')
                    require_role(user,{'admin','center'});
                    self.send_json({'ok':True,'photos':[dict(x) for x in db.execute('SELECT * FROM dive_point_photos WHERE dive_point_id=? ORDER BY sort_order,id',(pid,)).fetchall()]}); return
                if path.startswith('/api/dive-points/') and path.endswith('/centers'):
                    pid=int(path.split('/')[3]); p=db.execute('SELECT latitude,longitude FROM dive_points WHERE id=? AND active=1',(pid,)).fetchone()
                    if not p: self.send_json({'error':'Punto no encontrado'},404); return
                    rows=db.execute('''SELECT c.*, COALESCE((SELECT ROUND(AVG(cr.rating),1) FROM center_reviews cr WHERE cr.center_id=c.id AND cr.active=1),0) AS rating_average, (SELECT COUNT(*) FROM center_reviews cr WHERE cr.center_id=c.id AND cr.active=1) AS review_count FROM center_point_links cpl JOIN centers c ON c.id=cpl.center_id WHERE cpl.dive_point_id=? AND c.active=1 ORDER BY c.name''',(pid,)).fetchall()
                    mode='exact'
                    if not rows:
                        mode='nearby'; candidates=db.execute('''SELECT c.*, COALESCE((SELECT ROUND(AVG(cr.rating),1) FROM center_reviews cr WHERE cr.center_id=c.id AND cr.active=1),0) AS rating_average, (SELECT COUNT(*) FROM center_reviews cr WHERE cr.center_id=c.id AND cr.active=1) AS review_count FROM centers c WHERE c.active=1 AND c.latitude IS NOT NULL AND c.longitude IS NOT NULL''').fetchall()
                        from math import radians,sin,cos,asin,sqrt
                        def dist(a,b,c,d):
                            lat1,lon1,lat2,lon2=map(radians,[a,b,c,d]); x=sin((lat2-lat1)/2)**2+cos(lat1)*cos(lat2)*sin((lon2-lon1)/2)**2; return 6371*2*asin(sqrt(x))
                        nearby=[]
                        for c in candidates:
                            km=dist(float(p['latitude']),float(p['longitude']),float(c['latitude']),float(c['longitude']))
                            if km<=60: nearby.append((km,c))
                        nearby.sort(key=lambda x:(x[0],x[1]['name']))
                        self.send_json({'mode':mode,'items':[with_booking_flags(db,dict(center_row(c),distance_km=km)) for km,c in nearby[:12]]}); return
                    self.send_json({'mode':mode,'items':[with_booking_flags(db,center_row(r)) for r in rows]}); return
                if path == '/api/top-dives':
                    try:
                        lat = float(query.get('lat',[''])[0]); lon = float(query.get('lon',[''])[0])
                    except (TypeError, ValueError):
                        self.send_json({'error':'Necesitamos una ubicación válida para calcular el top 10.'},400); return
                    try: radius_km = max(5.0, min(500.0, float(query.get('radius',['80'])[0])))
                    except (TypeError, ValueError): radius_km = 80.0
                    self.send_json(top_dives(db, lat, lon, radius_km)); return
                if path.startswith('/api/dive-points/'):
                    pid = int(path.rsplit('/',1)[1])
                    r = db.execute('''SELECT p.*, c.name AS center_name, rc.name AS recommended_certification_name FROM dive_points p LEFT JOIN centers c ON c.id=p.center_id LEFT JOIN certifications rc ON rc.id=p.recommended_certification_id WHERE p.id=? AND p.active=1''',(pid,)).fetchone()
                    if not r: self.send_json({'error':'Punto no encontrado'},404); return
                    photos = db.execute('SELECT * FROM dive_point_photos WHERE dive_point_id=? ORDER BY sort_order,id',(pid,)).fetchall()
                    near=[]
                    try:
                        if r['latitude'] is not None and r['longitude'] is not None: near=nearby_points(db,float(r['latitude']),float(r['longitude']),80,exclude=pid,limit=6)
                    except (TypeError,ValueError): near=[]
                    snap_row=points_snapshot(db)['by_id'].get(pid) or {}
                    self.send_json({'item':point_row(r),'photos':[dict(x) for x in photos],'nearby':near,'types':snap_row.get('types',[])})
                    return
                if path == '/api/center-directory':
                    self.send_json(center_directory(db, query)); return
                if path == '/api/dive-types':
                    self.send_json(dive_types_overview(db)); return
                if path.startswith('/api/dive-types/'):
                    d=dive_type_detail(db, unquote(path.split('/',3)[3]))
                    if not d: self.send_json({'error':'Tipo de buceo no encontrado'},404); return
                    self.send_json(d); return
                if path == '/api/centers':
                    q = clean_text(query.get('q',[''])[0], 120)
                    country = clean_text(query.get('country',[''])[0], 120)
                    where=['c.active=1']; args=[]
                    if q:
                        like=f'%{fold_text(q)}%'; where.append('(fold(c.name) LIKE ? OR fold(c.city) LIKE ? OR fold(c.region) LIKE ? OR fold(c.specialties) LIKE ?)'); args += [like]*4
                    if country: where.append('c.country=?'); args.append(country)
                    order='c.name'
                    sort=clean_text(query.get('sort',[''])[0],40)
                    if sort=='rating': order='CASE WHEN review_count=0 THEN 1 ELSE 0 END, rating_average DESC, review_count DESC, c.name'
                    elif sort=='reviews': order='review_count DESC, rating_average DESC, c.name'
                    rows=db.execute('''SELECT c.*,
                                      (SELECT COUNT(*) FROM center_point_links cpl JOIN dive_points dp ON dp.id=cpl.dive_point_id WHERE cpl.center_id=c.id AND dp.active=1) AS point_count,
                                      COALESCE((SELECT ROUND(AVG(cr.rating),1) FROM center_reviews cr WHERE cr.center_id=c.id AND cr.active=1),0) AS rating_average,
                                      (SELECT COUNT(*) FROM center_reviews cr WHERE cr.center_id=c.id AND cr.active=1) AS review_count
                                      FROM centers c WHERE '''+' AND '.join(where)+' ORDER BY '+order,args).fetchall()
                    self.send_json({'items':[center_row(r) for r in rows]}); return
                if path.startswith('/api/bookings/') and (path.endswith('/receipt') or path.endswith('/receipt.pdf')):
                    user=require_user(self,db); bid=int(path.split('/')[3])
                    b=db.execute('SELECT user_id,center_id,provider_user_id FROM bookings WHERE id=?',(bid,)).fetchone()
                    if not b: self.send_json({'error':'Reserva no encontrada'},404); return
                    if b['user_id']!=user['id'] and not can_manage_booking(user,b): raise PermissionError('No puedes consultar esta reserva.')
                    lang=normalize_lang(clean_text(query.get('lang',[''])[0],5) or user_lang(db,user['id']))
                    raw=booking_pdf(db,bid,self.base_url(),lang)
                    if raw is None: self.send_json({'error':'Reserva no encontrada'},404); return
                    self.send_bytes(raw,'application/pdf',f'WORLDIVES-reserva-{bid}.pdf'); return
                if path == '/api/me/area':
                    user=require_user(self,db); uid=user['id']
                    bookings=db.execute('''SELECT b.*,COALESCE(c.name,pu.fullname) AS center_name,c.city,c.phone AS center_phone,COALESCE(c.email,pu.email) AS center_email,c.address AS center_address,p.name AS point_name,s.title AS service_title,s.response_hours
                                          FROM bookings b LEFT JOIN centers c ON c.id=b.center_id LEFT JOIN users pu ON pu.id=b.provider_user_id LEFT JOIN dive_points p ON p.id=b.dive_point_id LEFT JOIN provider_services s ON s.id=b.service_id
                                          WHERE b.user_id=? ORDER BY b.booking_date DESC,b.booking_time DESC,b.id DESC''',(uid,)).fetchall()
                    bookings=[dict(dict(x),**booking_view_status(x),mode_label=wbk.mode_label(x['booking_mode'] or 'request',x['response_hours'])) for x in bookings]
                    exps=db.execute('''SELECT eb.*,e.title,e.summary,e.start_date,e.end_date,e.price,e.currency,e.includes,e.conditions,
                                              t.title AS destination_title,c.name AS center_name,c.city,c.phone AS center_phone,c.email AS center_email,
                                              u.fullname AS provider_name
                                       FROM experience_bookings eb JOIN travel_experiences e ON e.id=eb.travel_experience_id
                                       JOIN travel_offers t ON t.id=e.travel_offer_id LEFT JOIN centers c ON c.id=e.center_id
                                       LEFT JOIN users u ON u.id=e.provider_user_id WHERE eb.user_id=?
                                       ORDER BY COALESCE(e.start_date,'9999-12-31'),eb.id DESC''',(uid,)).fetchall()
                    msgs=db.execute('''SELECT m.*,u.fullname AS sender_name,c.name AS booking_center_name
                                       FROM messages m JOIN users u ON u.id=m.sender_user_id LEFT JOIN bookings b ON b.id=m.booking_id
                                       LEFT JOIN centers c ON c.id=b.center_id LEFT JOIN users pu ON pu.id=b.provider_user_id WHERE m.recipient_user_id=? ORDER BY m.created_at DESC,m.id DESC''',(uid,)).fetchall()
                    unread=sum(1 for m in msgs if not m['read_at'])
                    self.send_json({'bookings':bookings,'experience_bookings':[dict(x) for x in exps],'messages':[dict(x) for x in msgs],'unread_messages':unread}); return
                if path == '/api/messages':
                    user=require_user(self,db); rows=db.execute('''SELECT m.*,u.fullname AS sender_name FROM messages m JOIN users u ON u.id=m.sender_user_id WHERE m.recipient_user_id=? ORDER BY m.created_at DESC,m.id DESC''',(user['id'],)).fetchall(); self.send_json({'items':[dict(x) for x in rows]}); return
                if path.startswith('/api/public/bookings/') and path.count('/')==4:
                    # G4: the booking check page (QR) needs the owner's or the centre's session, or the long random token
                    # printed in the QR / PDF. It never returns the user id nor the surname.
                    bid=int(path.rsplit('/',1)[1]); token=clean_text(query.get('t',[''])[0],80) or ''
                    b=db.execute("""SELECT b.id,b.user_id,b.center_id,b.provider_user_id,b.public_token,b.booking_date,b.booking_time,b.participants,b.status,b.payment_status,b.price,b.currency,
                                           COALESCE(b.contact_name,u.fullname) AS fullname,COALESCE(c.name,pu.fullname) AS center_name,c.city AS center_city,p.name AS point_name
                                    FROM bookings b JOIN users u ON u.id=b.user_id LEFT JOIN centers c ON c.id=b.center_id LEFT JOIN users pu ON pu.id=b.provider_user_id
                                    LEFT JOIN dive_points p ON p.id=b.dive_point_id WHERE b.id=?""",(bid,)).fetchone()
                    viewer=current_user(self,db)
                    allowed=bool(b) and ((token and b['public_token'] and wsec.constant_time_equals(token,b['public_token']))
                                         or (viewer and (viewer['id']==b['user_id'] or viewer['role']=='admin' or can_manage_booking(viewer,b))))
                    if not allowed: self.send_json({'error':'Reserva no encontrada'},404); return
                    d={k:b[k] for k in ('id','booking_date','booking_time','participants','status','payment_status','price','currency','center_name','center_city','point_name')}
                    d['customer']=short_name(b['fullname']); d['ref']=f"WOD-{b['id']:06d}"; d['status_label']=booking_status_label(b['status'])
                    self.send_json({'booking':d}); return
                if path.startswith('/api/bookings/') and path.endswith('/diver-sheet.pdf'):
                    user=require_user(self,db); bid=int(path.split('/')[3]); b=db.execute('SELECT user_id,center_id,provider_user_id FROM bookings WHERE id=?',(bid,)).fetchone()
                    if not b: self.send_json({'error':'Reserva no encontrada'},404); return
                    if b['user_id']!=user['id'] and not can_manage_booking(user,b): raise PermissionError('No puedes consultar esta ficha.')
                    if user['role'] in ('center','freelance') and b['user_id']!=user['id'] and not provider_can_see_user(db,b) and not is_guest_user(db,b['user_id']):
                        raise PermissionError('Este cliente no ha compartido su ficha de buceador con tu centro.')
                    if user['role']=='admin': audit(db,user['id'],'diver_sheet_viewed','booking',bid); db.commit()
                    raw=diver_sheet_pdf(db,bid,self.base_url()); self.send_bytes(raw,'application/pdf',f'WORLDIVES-ficha-buceador-{bid}.pdf'); return
                if path.startswith('/api/bookings/') and path.endswith('/qr.svg'):
                    user=require_user(self,db); bid=int(path.split('/')[3])
                    b=db.execute('SELECT user_id,center_id,provider_user_id FROM bookings WHERE id=?',(bid,)).fetchone()
                    if not b: self.send_json({'error':'Reserva no encontrada'},404); return
                    if b['user_id']!=user['id'] and not can_manage_booking(user,b): raise PermissionError('No puedes consultar esta reserva.')
                    self.send_bytes(qr_svg(booking_check_url(db,bid,self.base_url())),'image/svg+xml; charset=utf-8'); return
                if path.startswith('/api/bookings/') and path.count('/')==3:
                    user=require_user(self,db); bid=int(path.rsplit('/',1)[1])
                    b=db.execute('''SELECT b.*, u.fullname, u.email, u.username, COALESCE(c.name,pu.fullname) AS center_name, c.city AS center_city, c.phone AS center_phone, COALESCE(c.email,pu.email) AS center_email, c.website AS center_website, c.address AS center_address, p.name AS point_name, p.country AS point_country, p.dive_type AS point_dive_type, s.title AS service_title, s.response_hours
                                    FROM bookings b JOIN users u ON u.id=b.user_id LEFT JOIN centers c ON c.id=b.center_id LEFT JOIN users pu ON pu.id=b.provider_user_id
                                    LEFT JOIN user_profiles up ON up.user_id=u.id
                                    LEFT JOIN dive_points p ON p.id=b.dive_point_id LEFT JOIN provider_services s ON s.id=b.service_id WHERE b.id=?''',(bid,)).fetchone()
                    if not b: self.send_json({'error':'Reserva no encontrada'},404); return
                    if b['user_id']!=user['id'] and not can_manage_booking(user,b): raise PermissionError('No puedes consultar esta reserva.')
                    # G1/G5: the centre sees the diver's profile and documents only when the diver booked or shared them.
                    can_see=user['role']=='admin' or b['user_id']==user['id'] or provider_can_see_user(db,b) or is_guest_user(db,b['user_id'])
                    docs=db.execute('SELECT id,document_type,title,expires_at,status,original_name,uploaded_at FROM user_documents WHERE user_id=? ORDER BY expires_at IS NULL, expires_at',(b['user_id'],)).fetchall() if can_see else []
                    profile=None if not can_see else db.execute('''SELECT up.phone,up.country,up.city,up.preferred_language,up.notes,up.date_of_birth,up.emergency_contact_name,up.emergency_contact_phone,up.equipment_required,up.suit_type,up.suit_size,up.boot_size,up.bcd_size,up.fin_size,up.mask_size,up.usual_weight_kg,up.tank_preference,up.computer_preference,up.equipment_notes,c.name AS certification_name FROM user_profiles up LEFT JOIN certifications c ON c.id=up.certification_id WHERE up.user_id=?''',(b['user_id'],)).fetchone()
                    po=db.execute("SELECT id,status,amount,currency,created_at,paid_at,amount_received,receipt_url,card_brand,card_last4,provider_payment_id FROM payment_orders WHERE booking_id=? ORDER BY CASE status WHEN 'paid' THEN 0 ELSE 1 END, id DESC LIMIT 1",(bid,)).fetchone()
                    _svc,payee=booking_payee(db,b)
                    bd=dict(b); online=payee_ready(payee)
                    bd['provider']={'type':payee['type'],'id':payee['id'],'name':payee['name'],'legal_name':payee.get('legal_name') or '','tax_id':payee.get('tax_id') or '',
                                    'address':payee.get('fiscal_address') or ', '.join(x for x in (payee.get('address'),payee.get('city'),payee.get('country')) if x)} if payee else None
                    if not b['center_id'] and payee: bd['center_phone']=payee.get('phone'); bd['center_city']=payee.get('city')
                    is_provider=can_manage_booking(user,b) and b['user_id']!=user['id']
                    paid_,refunded_,orders_=booking_paid_online(db,bid)
                    bd['paid_online']=paid_; bd['refunded_online']=refunded_; bd['refundable']=round(max(0.0,paid_-refunded_),2)
                    if is_provider or user['role']=='admin' or b['user_id']==user['id']:
                        bd['refunds']=[dict(r) for r in db.execute('SELECT id,amount,currency,reason,note,status,source,created_at FROM payment_refunds WHERE booking_id=? ORDER BY id',(bid,)).fetchall()]
                    bd['center_online_payments']=online
                    st_=wbk.normalize_state(b['status'])
                    open_=(st_=='payment_in_progress' and (parse_local(b['hold_expires_at']) or local_now())>=local_now()) or (st_=='accepted_pending_payment' and (parse_local(b['payment_deadline']) or local_now())>=local_now())
                    bd['can_pay_online']=bool(online and b['user_id']==user['id'] and open_ and b['payment_status'] not in ('paid','deposit_paid') and float(b['price'] or 0)>0)
                    bd['pay_now']=float(b['deposit_amount'] or 0) if 0<float(b['deposit_amount'] or 0)<float(b['price'] or 0) else float(b['price'] or 0)
                    pay=dict(po) if po else None
                    if pay: pay['reference']=f"PAY-{pay['id']:05d}"; pay.pop('provider_payment_id',None)
                    if wbk.normalize_state(b['status']) in wbk.CANCELLABLE: bd['cancel']=booking_cancel_terms(db,b)
                    bd.update(booking_view_status(b)); bd['mode_label']=wbk.mode_label(b['booking_mode'] or 'request',b['response_hours'] if 'response_hours' in b.keys() else None)
                    _pol=booking_policy(db,b)
                    bd['cancellation_policy']=f"{_pol['free_hours']}h-{_pol['refund_pct']}"; bd['cancellation_text']=_pol['text']; bd['cancellation_note']=_pol['note']
                    bd['cancel_free_hours']=_pol['free_hours']; bd['cancel_refund_pct']=_pol['refund_pct']
                    bd.pop('public_token',None); bd['check_url']=booking_check_url(db,bid,self.base_url()) if (b['user_id']==user['id'] or can_manage_booking(user,b)) else None
                    self.send_json({'booking':bd,'payment':pay,'profile':dict(profile) if profile else {},'documents':[dict(x) for x in docs],'data_shared':bool(can_see)}); return
                if path == '/api/bookings':
                    user=require_user(self,db)
                    if user['role'] in ('center','freelance'):
                        # Optional server-side filters keep the payload small for centers with many bookings.
                        scope,args=provider_scope_sql(user)
                        where=[scope,"b.status<>'payment_in_progress'",CENTER_VISIBLE_SQL]
                        q_from=clean_text(query.get('from',[''])[0],10); q_to=clean_text(query.get('to',[''])[0],10)
                        if q_from: where.append('b.booking_date>=?'); args.append(q_from)
                        if q_to: where.append('b.booking_date<=?'); args.append(q_to)
                        q_status=clean_text(query.get('status',[''])[0],30)
                        if q_status=='pending': q_status='requested'
                        if q_status: where.append('b.status=?'); args.append(q_status)
                        q_pay=clean_text(query.get('payment',[''])[0],20)
                        if q_pay: where.append('b.payment_status=?'); args.append(q_pay)
                        q_service=int(query.get('service_id',['0'])[0] or 0)
                        if q_service: where.append('b.service_id=?'); args.append(q_service)
                        q_text=clean_text(query.get('q',[''])[0],80)
                        if q_text:
                            like=f'%{fold_text(q_text)}%'; where.append("(fold(u.fullname) LIKE ? OR fold(u.email) LIKE ? OR fold(b.contact_phone) LIKE ? OR fold(b.external_ref) LIKE ? OR fold(s.title) LIKE ? OR CAST(b.id AS TEXT)=?)"); args+= [like,like,like,like,like,q_text.lstrip('#')]
                        order='b.booking_date ASC,b.booking_time ASC,b.id ASC' if query.get('order',[''])[0]=='asc' else 'b.booking_date DESC,b.booking_time DESC,b.id DESC'
                        limit=max(1,min(5000,int(query.get('limit',['2000'])[0] or 2000)))
                        rows=db.execute(f'''SELECT b.*, COALESCE(b.contact_name,u.fullname) AS fullname, CASE WHEN u.email LIKE '%.local' THEN COALESCE(b.contact_email,'') ELSE u.email END AS email, u.username, COALESCE(c.name,pu.fullname) AS center_name, p.name AS point_name, s.title AS service_title, s.color AS service_color
                                             FROM bookings b JOIN users u ON u.id=b.user_id LEFT JOIN centers c ON c.id=b.center_id LEFT JOIN users pu ON pu.id=b.provider_user_id LEFT JOIN dive_points p ON p.id=b.dive_point_id
                                             LEFT JOIN provider_services s ON s.id=b.service_id WHERE {' AND '.join(where)} ORDER BY {order} LIMIT {limit}''',args).fetchall()
                    elif user['role']=='admin':
                        # The platform may hold hundreds of thousands of bookings: the admin list gets the most recent ones.
                        limit=max(1,min(5000,int(query.get('limit',['1000'])[0] or 1000)))
                        rows=db.execute('''SELECT b.*, u.fullname, u.email, u.username, COALESCE(c.name,pu.fullname) AS center_name, p.name AS point_name, s.title AS service_title FROM bookings b JOIN users u ON u.id=b.user_id LEFT JOIN centers c ON c.id=b.center_id LEFT JOIN users pu ON pu.id=b.provider_user_id LEFT JOIN dive_points p ON p.id=b.dive_point_id LEFT JOIN provider_services s ON s.id=b.service_id ORDER BY b.booking_date DESC,b.id DESC LIMIT ?''',(limit,)).fetchall()
                    else:
                        rows=db.execute('''SELECT b.*, COALESCE(c.name,pu.fullname) AS center_name, p.name AS point_name, s.title AS service_title FROM bookings b LEFT JOIN centers c ON c.id=b.center_id LEFT JOIN users pu ON pu.id=b.provider_user_id LEFT JOIN dive_points p ON p.id=b.dive_point_id LEFT JOIN provider_services s ON s.id=b.service_id WHERE b.user_id=? ORDER BY b.booking_date DESC,b.id DESC''',(user['id'],)).fetchall()
                    items=[]
                    for r_ in rows:
                        d=dict(r_); d.update(booking_view_status(r_)); d.pop('public_token',None) if user['role']!='recreational' else None
                        d['mode_label']=wbk.mode_label(d.get('booking_mode') or 'request')
                        items.append(d)
                    self.send_json({'items':items}); return
                if path == '/api/center/requests':
                    # «Solicitudes pendientes»: requests to accept or reject, with the time left to answer.
                    user=require_user(self,db); require_role(user,{'center','freelance'}); scope,sargs=provider_scope_sql(user)
                    rows=db.execute(f'''SELECT b.id,b.booking_date,b.booking_time,b.participants,b.price,b.currency,b.notes,b.response_deadline,b.created_at,b.payment_status,
                                              COALESCE(b.contact_name,u.fullname) AS fullname,s.title AS service_title,s.color AS service_color,p.name AS point_name,ss.spots_available
                                         FROM bookings b JOIN users u ON u.id=b.user_id LEFT JOIN provider_services s ON s.id=b.service_id
                                         LEFT JOIN dive_points p ON p.id=b.dive_point_id LEFT JOIN service_slots ss ON ss.id=b.slot_id
                                        WHERE {scope} AND b.status IN ('requested','pending') ORDER BY COALESCE(b.response_deadline,'9999'),b.id''',sargs).fetchall()
                    now_l=local_now(); items=[]
                    for r_ in rows:
                        d=dict(r_); dl=parse_local(d['response_deadline'])
                        d['minutes_left']=max(0,int((dl-now_l).total_seconds()//60)) if dl else None
                        d['enough_spots']=d['spots_available'] is None or int(d['spots_available'])>=int(d['participants'] or 1)
                        items.append(d)
                    awaiting=db.execute(f"SELECT COUNT(*) FROM bookings b WHERE {scope} AND b.status='accepted_pending_payment'",sargs).fetchone()[0]
                    refunds=db.execute(f"SELECT COUNT(*) FROM bookings b WHERE {scope} AND b.refund_status IN ('proposed','failed')",sargs).fetchone()[0]
                    self.send_json({'items':items,'count':len(items),'awaiting_payment':awaiting,'pending_refunds':refunds}); return
                if path == '/api/account/documents':
                    user=require_user(self,db)
                    rows=db.execute('SELECT id,document_type,title,original_name,expires_at,status,uploaded_at FROM user_documents WHERE user_id=? ORDER BY expires_at IS NULL, expires_at',(user['id'],)).fetchall()
                    self.send_json({'items':[dict(r) for r in rows]}); return
                if path.startswith('/api/documents/file/'):
                    # G1: owner; a centre only while the diver has a live booking made by himself with it (or shared his
                    # data); the administrator with a record in the audit log. Every download is logged.
                    user=require_user(self,db); did=int(path.rsplit('/',1)[1]); doc=db.execute('SELECT * FROM user_documents WHERE id=?',(did,)).fetchone()
                    if not doc: self.send_json({'error':'Documento no encontrado'},404); return
                    own=doc['user_id']==user['id']
                    if not own:
                        if user['role']=='admin': pass
                        elif user['role']=='center' and user['center_id'] and center_can_see_user(db,user['center_id'],doc['user_id']): pass
                        else:
                            audit(db,user['id'],'document_access_denied','user_document',did,{'owner':doc['user_id']}); db.commit()
                            raise PermissionError('No tienes acceso a este documento.')
                    file_path=document_file_path(doc['file_path'])
                    if not file_path or not file_path.exists(): self.send_json({'error':'El archivo ya no está disponible.'},404); return
                    audit(db,user['id'],'document_downloaded','user_document',did,{'owner':doc['user_id'],'as':'owner' if own else user['role'],'center_id':user.get('center_id') if user['role']=='center' else None}); db.commit()
                    self.send_private_file(file_path,doc['original_name'] or file_path.name,inline=query.get('download',['0'])[0]!='1'); return
                if path == '/api/logbook':
                    user=require_user(self,db)
                    rows=db.execute('SELECT * FROM logbook_entries WHERE user_id=? ORDER BY dive_date DESC,id DESC',(user['id'],)).fetchall()
                    self.send_json({'items':[dict(r) for r in rows]}); return
                if path == '/api/wallet':
                    user=require_user(self,db)
                    sync_user_rewards(db,user['id']); db.commit()
                    rows=db.execute('SELECT * FROM wallet_transactions WHERE user_id=? ORDER BY created_at DESC,id DESC',(user['id'],)).fetchall()
                    total=db.execute('SELECT COALESCE(SUM(amount),0) FROM wallet_transactions WHERE user_id=?',(user['id'],)).fetchone()[0]
                    red=db.execute('''SELECT rr.*, ro.title, ro.reward_type, c.name AS center_name FROM reward_redemptions rr JOIN reward_offers ro ON ro.id=rr.offer_id LEFT JOIN centers c ON c.id=ro.center_id WHERE rr.user_id=? ORDER BY rr.created_at DESC,rr.id DESC''',(user['id'],)).fetchall()
                    self.send_json({'balance':round(float(total or 0),2),'items':[dict(r) for r in rows],'redemptions':[dict(r) for r in red]}); return
                if path == '/api/rewards':
                    user=require_user(self,db)
                    sync_user_rewards(db,user['id']); db.commit()
                    events=db.execute('SELECT * FROM reward_events WHERE user_id=? ORDER BY created_at DESC,id DESC',(user['id'],)).fetchall()
                    total=db.execute('SELECT COALESCE(SUM(points),0) FROM reward_events WHERE user_id=?',(user['id'],)).fetchone()[0]
                    dive_count=db.execute('SELECT COUNT(*) FROM logbook_entries WHERE user_id=?',(user['id'],)).fetchone()[0]
                    centers_count=db.execute('SELECT COUNT(DISTINCT center_id) FROM center_links WHERE user_id=?',(user['id'],)).fetchone()[0]
                    offers=db.execute('''SELECT ro.*, c.name AS center_name FROM reward_offers ro LEFT JOIN centers c ON c.id=ro.center_id WHERE ro.active=1 AND (ro.stock IS NULL OR ro.stock>0) ORDER BY ro.center_id IS NOT NULL, ro.cost_wallet, ro.id''').fetchall()
                    red=db.execute('''SELECT rr.*, ro.title, ro.reward_type, c.name AS center_name FROM reward_redemptions rr JOIN reward_offers ro ON ro.id=rr.offer_id LEFT JOIN centers c ON c.id=ro.center_id WHERE rr.user_id=? ORDER BY rr.created_at DESC,rr.id DESC''',(user['id'],)).fetchall()
                    level=reward_level(int(total or 0))
                    self.send_json({'points':int(total or 0),'level':level,'stats':{'dives':dive_count,'centers':centers_count},'items':[dict(r) for r in events],'offers':[reward_offer_row(r) for r in offers],'redemptions':[dict(r) for r in red]}); return
                if path == '/api/rewards/offers':
                    user=require_user(self,db)
                    rows=db.execute('''SELECT ro.*, c.name AS center_name FROM reward_offers ro LEFT JOIN centers c ON c.id=ro.center_id WHERE ro.active=1 AND ro.center_id IS NOT NULL AND (ro.stock IS NULL OR ro.stock>0) ORDER BY ro.cost_wallet,ro.id''').fetchall()
                    self.send_json({'items':[dict(r) for r in rows]}); return
                if path == '/api/provider/reward-offers':
                    user=require_user(self,db); require_role(user,{'admin','center'})
                    if user['role']=='admin':
                        rows=db.execute('SELECT ro.*, c.name AS center_name FROM reward_offers ro LEFT JOIN centers c ON c.id=ro.center_id ORDER BY ro.active DESC,ro.created_at DESC').fetchall()
                    else:
                        rows=db.execute('SELECT ro.*, c.name AS center_name FROM reward_offers ro LEFT JOIN centers c ON c.id=ro.center_id WHERE ro.center_id=? ORDER BY ro.active DESC,ro.created_at DESC',(user['center_id'],)).fetchall()
                    self.send_json({'items':[dict(r) for r in rows]}); return
                if path == '/api/admin/center-claims':
                    user=require_user(self,db); require_role(user,{'admin'})
                    rows=db.execute('''SELECT cc.*,u.fullname,u.email,u.username,c.name AS matched_center_name,c.website AS draft_website,
                                              sc.name AS suggested_center_name,sc.city AS suggested_center_city,sc.phone AS suggested_center_phone,sc.website AS suggested_center_website
                                         FROM center_claims cc JOIN users u ON u.id=cc.user_id LEFT JOIN centers c ON c.id=cc.center_id LEFT JOIN centers sc ON sc.id=cc.suggested_center_id
                                        WHERE cc.status='pending' ORDER BY cc.created_at DESC''').fetchall()
                    items=[]
                    for r_ in rows:
                        d=dict(r_); dom=(d.get('email') or '').rsplit('@',1)[-1].lower(); site=urlparse(d.get('website') or d.get('draft_website') or '').hostname or ''
                        d['email_matches_domain']=bool(dom and site and (site==dom or site.endswith('.'+dom) or dom.endswith('.'+site.removeprefix('www.')) or site.removeprefix('www.')==dom))
                        items.append(d)
                    self.send_json({'items':items,'methods':VERIFICATION_METHODS}); return
                if path == '/api/admin/users':
                    user=require_user(self,db); require_role(user,{'admin'})
                    rows=db.execute('''SELECT u.id,u.fullname,u.email,u.username,u.role,u.center_id,u.created_at,u.last_login,c.name AS center_name FROM users u LEFT JOIN centers c ON c.id=u.center_id ORDER BY u.created_at DESC''').fetchall()
                    self.send_json({'items':[dict(r) for r in rows]}); return
                if path == '/api/admin/suggestions':
                    user=require_user(self,db); require_role(user,{'admin'})
                    rows=db.execute('''SELECT s.*, p.name AS point_name, u.fullname, u.email FROM point_position_suggestions s JOIN dive_points p ON p.id=s.dive_point_id JOIN users u ON u.id=s.user_id WHERE s.status='pending' ORDER BY s.created_at DESC''').fetchall()
                    self.send_json({'items':[dict(r) for r in rows]}); return
                if path == '/api/admin/qr':
                    user=require_user(self,db); require_role(user,{'admin'})
                    rows=db.execute('''SELECT q.*, c.name AS center_name FROM qr_codes q JOIN centers c ON c.id=q.center_id ORDER BY q.created_at DESC''').fetchall()
                    self.send_json({'items':[dict(r) for r in rows]}); return
                if path == '/api/admin/virtual-experiences':
                    user=require_user(self,db); require_role(user,{'admin'})
                    rows=db.execute('''SELECT v.*, p.name AS point_name, p.country, p.region, u.fullname AS created_by_name FROM virtual_experiences v JOIN dive_points p ON p.id=v.dive_point_id LEFT JOIN users u ON u.id=v.created_by_user_id WHERE v.active=1 ORDER BY v.updated_at DESC, v.id DESC''').fetchall()
                    self.send_json({'items':[dict(r) for r in rows]}); return
                if path == '/api/admin/audit':
                    user=require_user(self,db); require_role(user,{'admin'})
                    rows=db.execute('''SELECT a.*, u.fullname FROM audit_log a LEFT JOIN users u ON u.id=a.user_id ORDER BY a.id DESC LIMIT 300''').fetchall()
                    self.send_json({'items':[dict(r) for r in rows]}); return
                if path.startswith('/api/center/clients'):
                    user=require_user(self,db); require_role(user,{'center','admin'})
                    cid = user['center_id'] if user['role']=='center' else int(query.get('center_id',['0'])[0] or 0)
                    if not cid: self.send_json({'items':[]}); return
                    # A client is anyone who booked with the center or checked in with its QR.
                    rows=db.execute('''WITH b AS (SELECT user_id, COUNT(*) AS bookings_count, MAX(booking_date) AS last_booking, MIN(booking_date) AS first_booking,
                                                     SUM(CASE WHEN payment_status='paid' THEN price ELSE 0 END) AS total_paid, MAX(contact_phone) AS phone
                                                FROM bookings WHERE center_id=? AND status NOT IN ('rejected') GROUP BY user_id),
                                           ids AS (SELECT user_id FROM b UNION SELECT user_id FROM center_links WHERE center_id=?)
                                      SELECT u.id,u.fullname,u.email,u.username,COALESCE(b.phone,up.phone) AS phone,cl.first_checkin,cl.last_checkin,
                                             COALESCE(b.bookings_count,0) AS bookings_count,b.first_booking,b.last_booking,COALESCE(b.total_paid,0) AS total_paid
                                        FROM ids JOIN users u ON u.id=ids.user_id LEFT JOIN b ON b.user_id=u.id
                                        LEFT JOIN center_links cl ON cl.user_id=u.id AND cl.center_id=?
                                        LEFT JOIN user_profiles up ON up.user_id=u.id
                                       ORDER BY COALESCE(b.last_booking,cl.last_checkin) DESC LIMIT 2000''',(cid,cid,cid)).fetchall()
                    items=[]
                    for r_ in rows:
                        d=dict(r_)
                        d['data_shared']=is_guest_user(db,d['id']) or center_can_see_user(db,cid,d['id'])
                        if not d['data_shared']: d['phone']=db.execute('SELECT MAX(contact_phone) FROM bookings WHERE center_id=? AND user_id=?',(cid,d['id'])).fetchone()[0]
                        if str(d.get('email') or '').endswith('.local'): d['email']=db.execute("SELECT MAX(contact_email) FROM bookings WHERE center_id=? AND user_id=?",(cid,d['id'])).fetchone()[0] or ''
                        items.append(d)
                    self.send_json({'items':items}); return
                if path.startswith('/api/qr/'):
                    # Generate a real SVG QR for the current local origin.
                    code=path.rsplit('/',1)[1]
                    qr=db.execute('''SELECT q.*,c.name AS center_name FROM qr_codes q JOIN centers c ON c.id=q.center_id WHERE q.code=? AND q.active=1''',(code,)).fetchone()
                    if not qr: self.send_error(404); return
                    try:
                        sys.path.insert(0, str(ROOT/'vendor'))
                        import qrcode
                        from qrcode.image.svg import SvgPathImage
                        payload=f'{self.base_url()}/#/checkin/{code}'
                        img=qrcode.make(payload,image_factory=SvgPathImage)
                        import io
                        buff=io.BytesIO(); img.save(buff)
                        raw=buff.getvalue()
                        self.send_bytes(raw,'image/svg+xml; charset=utf-8')
                    except Exception as e:
                        log_exception(self,e); self.send_json({'error':'No se pudo generar el QR.'},500)
                    return
                if path=='/api/payments/connect-status':
                    user=require_user(self,db); require_role(user,{'center','freelance','admin'})
                    payee=self_payee(db,user,{k:v[0] for k,v in query.items()})
                    ready=bool(payee['stripe_account_id'] and payee['stripe_charges_enabled'] and payee['stripe_payouts_enabled'])
                    self.send_json({'configured':bool(payee['stripe_account_id']),'charges_enabled':bool(payee['stripe_charges_enabled']),'payouts_enabled':bool(payee['stripe_payouts_enabled']),
                                    'details_submitted':bool(payee['stripe_details_submitted']),'ready':ready,'platform_ready':bool(stripe_secret()),'payee_type':payee['type'],
                                    'center_id':payee['id'] if payee['type']=='center' else None,'center_name':payee['name'],'dashboard':stripe_controller()['stripe_dashboard']['type'],
                                    'webhooks':{'platform':bool(os.environ.get('STRIPE_WEBHOOK_SECRET','').strip()),'connect':bool(os.environ.get('STRIPE_CONNECT_WEBHOOK_SECRET','').strip())}}); return
                # Unknown API routes answer JSON, never the SPA page (otherwise the client silently gets empty data).
                if path.startswith('/api/'):
                    self.send_json({'error':'Endpoint no encontrado'},404); return
                # Static: SPA fallback for every app route.
                self.serve_spa()
            except (BrokenPipeError, ConnectionResetError):
                return
            except PermissionError as e:
                db.rollback()  # never persist half-done work when a request fails
                self.send_json({'error':str(e)},403)
            except ValueError as e:
                db.rollback()  # never persist half-done work when a request fails
                self.send_json({'error':str(e)},400)
            except KeyError as e:
                # A required field is missing in the request: the client's fault, not a server error.
                db.rollback()
                self.send_json({'error':f'Falta un dato obligatorio: {e.args[0] if e.args else ""}.'},400)
            except TypeError as e:
                db.rollback()
                log_exception(self, e)
                self.send_json({'error':'Algún dato enviado no tiene el formato esperado.'},400)
            except Exception as e:
                db.rollback()  # never persist half-done work when a request fails
                log_exception(self, e)
                payload={'error':'Error interno'}
                if os.environ.get('WOD_DEBUG','').strip().lower() in {'1','true','yes','on'}:
                    payload['detail']=str(e)
                self.send_json(payload,500)

    def serve_spa(self):
        """index.html with the language of ?lang= in <html lang>, and hreflang alternates for the 10 languages (SEO)."""
        lang=normalize_lang((parse_qs(urlparse(self.path).query).get('lang',['es'])[0] or 'es')[:5])
        raw=(PUBLIC/'index.html').read_text(encoding='utf-8')
        base=wcfg.public_url() or self.base_url()
        alts=''.join(f'<link rel="alternate" hreflang="{HTML_LANG.get(l,l)}" href="{html.escape(base)}/?lang={l}">' for l in MAIL_LANGS)
        alts+=f'<link rel="alternate" hreflang="x-default" href="{html.escape(base)}/">'
        if wcfg.demo_mode(): alts+='<meta name="robots" content="noindex,nofollow">'
        raw=raw.replace('<html lang="es">',f'<html lang="{HTML_LANG.get(lang,lang)}">',1).replace('<!--hreflang-->',alts,1)
        body=raw.encode('utf-8')
        self.send_bytes(body,'text/html; charset=utf-8',cache='no-cache',inline=True)

    def precheck_write(self):
        """Runs before any state-changing request: CSRF origin check (G10), maintenance mode and the body size
        limit read from Content-Length before a single byte of the body is read (G7). Returns False when it answered."""
        path=urlparse(self.path).path
        try:
            self.enforce_same_origin()
        except (BrokenPipeError, ConnectionResetError):
            return False
        except PermissionError as e:
            self.send_json({'error':str(e)},403); return False
        ctype=(self.headers.get('Content-Type') or '').lower()
        limit=MAX_UPLOAD if ctype.startswith('multipart/') else (wcfg.MAX_WEBHOOK_BYTES if path.startswith('/api/payments/webhook') else MAX_BODY)
        try:
            body_length(self,limit)
        except BodyTooLarge as e:
            self.close_connection=True; self.send_json({'error':str(e)},413); return False
        except ValueError as e:
            self.close_connection=True; self.send_json({'error':str(e)},400); return False
        return True

    def do_POST(self):
        parsed=urlparse(self.path); path=parsed.path
        if not self.precheck_write(): return
        with connect() as db:
            try:
                if path=='/api/payments/webhook':
                    stripe_webhook(self,db,'STRIPE_WEBHOOK_SECRET',False); return
                if path=='/api/payments/webhook/connect':
                    # Events of the connected accounts (direct charges, refunds, disputes, account changes).
                    stripe_webhook(self,db,'STRIPE_CONNECT_WEBHOOK_SECRET',True); return
                if path in ('/api/payments/connect/onboard','/api/payments/connect/refresh','/api/payments/connect/sync','/api/payments/connect/login','/api/payments/connect/unlink'):
                    user=require_user(self,db); require_role(user,{'center','freelance','admin'}); data=json_body(self)
                    payee=self_payee(db,user,data)
                    if not stripe_secret(): raise ValueError('Los cobros online todavía no están activados en WORLDIVES (el administrador debe configurar la clave de Stripe en el servidor).')
                    table=payee_table(payee); base=public_site_url(); back=f'{base}/#/pagos?stripe='
                    action=path.rsplit('/',1)[1]
                    try:
                        stripe=stripe_module()
                        if action=='unlink':
                            # Admin only: forget an old account (for example an Express test account) so the provider can connect a new one.
                            require_role(user,{'admin'})
                            db.execute(f'UPDATE {table} SET stripe_account_id=NULL,stripe_charges_enabled=0,stripe_payouts_enabled=0,stripe_details_submitted=0 WHERE id=?',(payee['id'],))
                            audit(db,user['id'],'stripe_account_unlinked',payee['type'],payee['id'],{'account':payee['stripe_account_id']}); db.commit()
                            self.send_json({'ok':True}); return
                        account_id=payee['stripe_account_id']
                        if action=='onboard' and not account_id:
                            country=(payee.get('country') or 'ES').strip()
                            country=COUNTRY_ISO.get(country.lower(),country[:2].upper()) if len(country)!=2 else country.upper()
                            account=stripe.Account.create(
                                country=country, email=payee.get('email') if mail_deliverable(payee.get('email')) else None,
                                controller=stripe_controller(), capabilities=stripe_capabilities(),
                                business_profile={'name':payee['name'],'url':payee.get('website') or None,'mcc':'7999'},
                                metadata={'wod_payee':f"{payee['type']}:{payee['id']}"},
                                idempotency_key=f"wod-account-{payee['type']}-{payee['id']}")
                            account_id=account.id
                            db.execute(f'UPDATE {table} SET stripe_account_id=? WHERE id=?',(account_id,payee['id']))
                            audit(db,user['id'],'stripe_account_created',payee['type'],payee['id'],{'account':account_id}); db.commit()
                        if action in ('onboard','refresh'):
                            if not account_id: raise ValueError('Todavía no tienes una cuenta de cobros.')
                            link=stripe.AccountLink.create(account=account_id,type='account_onboarding',refresh_url=back+'refresh',return_url=back+'return')
                            self.send_json({'ok':True,'url':link.url,'account_id':account_id}); return
                        if not account_id: raise ValueError('Primero configura los cobros.')
                        if action=='sync':
                            a=stripe.Account.retrieve(account_id)
                            db.execute(f'UPDATE {table} SET stripe_charges_enabled=?,stripe_payouts_enabled=?,stripe_details_submitted=? WHERE id=?',(1 if a.get('charges_enabled') else 0,1 if a.get('payouts_enabled') else 0,1 if a.get('details_submitted') else 0,payee['id']))
                            if not (a.get('charges_enabled') and a.get('payouts_enabled')): warn_payment_mode_without_payments(db,payee['id'] if payee['type']=='center' else None,payee['id'] if payee['type']=='freelance' else None)
                            db.commit()
                            self.send_json({'ok':True,'charges_enabled':bool(a.get('charges_enabled')),'payouts_enabled':bool(a.get('payouts_enabled')),'details_submitted':bool(a.get('details_submitted')),'ready':bool(a.get('charges_enabled') and a.get('payouts_enabled'))}); return
                        if action=='login':
                            # Accounts with the full Stripe Dashboard sign in at dashboard.stripe.com; Express accounts get a login link.
                            if stripe_controller()['stripe_dashboard']['type']=='full': self.send_json({'ok':True,'url':'https://dashboard.stripe.com/','full_dashboard':True}); return
                            link=stripe.Account.create_login_link(account_id); self.send_json({'ok':True,'url':link.url}); return
                    except ValueError: raise
                    except ImportError: raise ValueError('Falta instalar la dependencia stripe en el servidor.')
                    except Exception as exc: raise ValueError(f'Stripe no ha podido completar la operación: {getattr(exc,"user_message",None) or exc}')
                if path=='/api/setup':
                    # G9: the web installer only works with WOD_ALLOW_SETUP=1 and while there is no administrator.
                    # In production the first administrator is created with: python app/server.py --create-admin
                    if not setup_allowed(): self.send_json({'error':'La instalación desde la web está desactivada. Crea el administrador con «python app/server.py --create-admin».'},403); return
                    if db.execute("SELECT 1 FROM users WHERE role='admin' LIMIT 1").fetchone():
                        self.send_json({'error':'La instalación ya está configurada.'},400); return
                    if REGISTER_LIMIT.hit('setup:'+self.client_ip()): self.send_json({'error':'Demasiados intentos. Espera un poco.'},429); return
                    data=json_body(self)
                    fullname=clean_text(data.get('fullname'),120); email=(clean_text(data.get('email'),160) or '').lower(); username=clean_text(data.get('username'),80); password=str(data.get('password',''))
                    if not fullname or not email or not username: raise ValueError('Completa nombre, email, usuario y contraseña.')
                    check_new_password(password)
                    cur=db.execute('INSERT INTO users(fullname,email,username,password_hash,role,created_at) VALUES(?,?,?,?,?,?)',(fullname,email,username,hash_password(password),'admin',now())); uid=cur.lastrowid
                    db.execute('INSERT INTO user_profiles(user_id,updated_at) VALUES(?,?)',(uid,now())); db.execute('UPDATE users SET terms_version=?,terms_accepted_at=?,pro_terms_version=?,pro_terms_accepted_at=? WHERE id=?',(LEGAL_VERSION,now(),LEGAL_VERSION,now(),uid)); audit(db,uid,'setup_completed'); db.commit()
                    self.login_user(uid,db); return
                if path=='/api/auth/register':
                    # G2: nobody becomes a centre or a professional by registering. The account starts as a diver
                    # ('recreational') with a pending request; the administrator verifies it (email on the centre's
                    # domain, a phone call to the public number or a document) and only then grants the role.
                    # A phone number that matches a centre is stored as a SUGGESTION for the administrator, never as a link.
                    if not registration_open(): raise PermissionError('El registro de cuentas nuevas no está abierto en esta versión.')
                    if REGISTER_LIMIT.hit('register:'+self.client_ip()): self.send_json({'error':'Demasiados registros desde esta conexión. Inténtalo más tarde.'},429); return
                    data=json_body(self); fullname=clean_text(data.get('fullname'),120); email=(clean_text(data.get('email'),160) or '').lower(); username=clean_text(data.get('username'),80); password=str(data.get('password',''))
                    requested=clean_text(data.get('account_type'),30) or 'recreational'
                    phone=clean_text(data.get('phone'),60); requested_center_name=clean_text(data.get('center_name'),180); city=clean_text(data.get('city'),100); center_note=clean_text(data.get('center_note'),2000)
                    website=wsec.clean_http_url(data.get('website'),250) if data.get('website') else None
                    if requested=='admin': raise PermissionError('Las cuentas de administración no se crean desde el registro.')
                    if requested not in {'recreational','center','freelance'}: requested='recreational'
                    if not fullname or not email or not username: raise ValueError('Completa todos los campos.')
                    if not re.fullmatch(r'[A-Za-z0-9._-]{3,40}',username): raise ValueError('El nombre de usuario solo puede tener letras, números, punto, guion y guion bajo (3 a 40).')
                    check_new_password(password)
                    if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+',email): raise ValueError('Escribe un email válido.')
                    if not data.get('accept_terms'): raise ValueError('Para crear la cuenta tienes que aceptar las condiciones de uso y la política de privacidad.')
                    if requested in {'center','freelance'} and not data.get('accept_pro_terms'): raise ValueError('Para crear una cuenta profesional tienes que aceptar las condiciones para centros y profesionales.')
                    if requested in {'center','freelance'}: pro_signup_check(db,data)
                    if requested=='center' and not requested_center_name: raise ValueError('Indica el nombre del centro de buceo.')
                    if requested in {'center','freelance'} and not phone: raise ValueError('Indica un teléfono de contacto para verificar tu cuenta profesional.')
                    if db.execute('SELECT 1 FROM users WHERE lower(email)=? AND password_hash<>? AND NOT (username LIKE ? ESCAPE ? AND last_login IS NULL)',(email,'!','web\\_%','\\')).fetchone() or db.execute('SELECT 1 FROM users WHERE lower(username)=lower(?)',(username,)).fetchone():
                        raise ValueError('Ya existe una cuenta con ese email o nombre de usuario. Si es tuya, inicia sesión o recupera la contraseña.')
                    reg_lang=normalize_lang(clean_text(data.get('lang'),5) or 'es')
                    # A customer record created by a center (manual booking / web import) never had a password.
                    # Without email verification we do not merge it into the new account: we free the email
                    # and keep that record (and its bookings) for the center only.
                    guest=db.execute("SELECT id FROM users WHERE lower(email)=? AND (password_hash='!' OR (username LIKE 'web\\_%' ESCAPE '\\' AND last_login IS NULL))",(email,)).fetchone()
                    if guest: db.execute('UPDATE users SET email=? WHERE id=?',(f'cliente-{guest["id"]}-{secrets.token_hex(4)}@sin-email.worldives.local',guest['id']))
                    uid=db.execute('INSERT INTO users(fullname,email,username,password_hash,role,requested_role,created_at) VALUES(?,?,?,?,?,?,?)',(fullname,email,username,hash_password(password),'recreational',requested,now())).lastrowid
                    db.execute('INSERT INTO user_profiles(user_id,phone,city,preferred_language,updated_at) VALUES(?,?,?,?,?)',(uid,phone,city,reg_lang,now()))
                    record_acceptances(db,uid,['terminos','privacidad'],self.client_ip())
                    if requested in {'center','freelance'}: record_acceptances(db,uid,['centros'],self.client_ip())
                    set_marketing_consent(db,uid,bool(data.get('accept_marketing')),self.client_ip())
                    claim_id=None; suggested=None
                    if requested in {'center','freelance'}:
                        norm=''.join(ch for ch in (phone or '') if ch.isdigit())
                        if len(norm)>=6:
                            for c in db.execute('SELECT id,name,city,phone FROM centers WHERE active=1').fetchall():
                                c_norm=''.join(ch for ch in (c['phone'] or '') if ch.isdigit())
                                if c_norm and (norm==c_norm or norm.endswith(c_norm[-9:]) or c_norm.endswith(norm[-9:])): suggested=c; break
                        draft_id=None
                        if requested=='center':
                            # Always a NEW centre, hidden (active=0) until the administrator approves it.
                            draft_id=db.execute('''INSERT INTO centers(name,country,region,city,address,website,phone,email,description,specialties,latitude,longitude,active,created_at,updated_at,verification_status,data_confidence,source_name)
                                                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,0,?,?,'pending_provider','provider_submitted','WORLDIVES DISCOVERY provider')''',
                                                (unique_center_name(db,requested_center_name,city),clean_text(data.get('country'),100) or 'España',None,city,None,website,phone,email,None,None,None,None,now(),now())).lastrowid
                        claim_id=db.execute('''INSERT INTO center_claims(user_id,center_id,requested_center_name,phone,city,website,note,status,created_at,requested_role,suggested_center_id,email)
                                               VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''',(uid,draft_id,requested_center_name or fullname,phone,city,website,center_note,'pending',now(),requested,suggested['id'] if suggested else None,email)).lastrowid
                    notify_user(db,uid,'welcome_pro' if requested in {'center','freelance'} else 'welcome',related=('user',uid))
                    send_email_verification(db,uid)
                    if requested in {'center','freelance'}:
                        notify_admins(db,'admin_new_pro',{'pro_name':fullname,'pro_email':email,'pro_type':'centro de buceo' if requested=='center' else 'profesional freelance','center':requested_center_name or fullname},('user',uid))
                    audit(db,uid,'register','user',uid,{'requested_role':requested,'center_claim_id':claim_id,'suggested_center_id':suggested['id'] if suggested else None,'ip':wsec.ip_hash(self.client_ip())}); db.commit()
                    self.login_user(uid,db,{'ok':True,'role':'recreational','requested_role':requested,'provider_verification':'pending' if requested in {'center','freelance'} else None}); return
                if path=='/api/auth/login':
                    data=json_body(self); login=(clean_text(data.get('login'),160) or '').lower(); password=str(data.get('password',''))[:256]
                    ip=self.client_ip(); rate_key=f'{ip}:{login}'; ip_key=f'ip:{ip}'
                    # Per account+IP (8 per 15 min) and per IP (5x that), so one address cannot try many accounts.
                    if login_rate_limited(rate_key) or LOGIN_IP_LIMIT.blocked(ip_key):
                        self.send_json({'error':'Demasiados intentos. Espera unos minutos y vuelve a intentarlo.'},429); return
                    user=db.execute('SELECT * FROM users WHERE lower(email)=? OR lower(username)=?',(login,login)).fetchone()
                    if not user or not verify_password(password,user['password_hash']):
                        record_login_failure(rate_key); LOGIN_IP_LIMIT.hit(ip_key); self.send_json({'error':'Usuario o contraseña incorrectos.'},401); return
                    clear_login_failures(rate_key)
                    if wsec.needs_rehash(user['password_hash']):
                        # Accounts from before v50.31 move to PBKDF2 with 600 000 iterations on their next login.
                        db.execute('UPDATE users SET password_hash=? WHERE id=?',(hash_password(password),user['id']))
                    second=login_second_factor(db,user,data)
                    if second: db.commit(); self.send_json(second); return
                    db.execute('UPDATE users SET last_login=? WHERE id=?',(now(),user['id'])); audit(db,user['id'],'login',details={'ip':wsec.ip_hash(ip)}); db.commit(); self.login_user(user['id'],db); return
                if path=='/api/auth/verify-email':
                    token=str(json_body(self).get('token') or '')[:200]
                    if FORGOT_LIMIT.hit('verify:'+self.client_ip()): self.send_json({'error':'Demasiados intentos. Espera unos minutos.'},429); return
                    th=hashlib.sha256(token.encode()).hexdigest()
                    row=db.execute('SELECT * FROM email_verifications WHERE token_hash=?',(th,)).fetchone()
                    if not row or row['used_at'] or row['expires_at']<now(): raise ValueError('El enlace no es válido o ha caducado. Pide uno nuevo desde «Mi cuenta».')
                    if db.execute('UPDATE email_verifications SET used_at=? WHERE token_hash=? AND used_at IS NULL',(now(),th)).rowcount!=1: raise ValueError('Este enlace ya se ha utilizado.')
                    u=db.execute('SELECT email FROM users WHERE id=?',(row['user_id'],)).fetchone()
                    changed=bool(u and u['email'].lower()!=row['email'].lower())
                    if changed:
                        if db.execute('SELECT 1 FROM users WHERE lower(email)=? AND id<>?',(row['email'].lower(),row['user_id'])).fetchone(): raise ValueError('Ese email ya lo usa otra cuenta.')
                        db.execute('UPDATE users SET email=?,email_verified_at=? WHERE id=?',(row['email'].lower(),now(),row['user_id']))
                        db.execute('DELETE FROM sessions WHERE user_id=?',(row['user_id'],))
                    else:
                        db.execute('UPDATE users SET email_verified_at=? WHERE id=?',(now(),row['user_id']))
                    audit(db,row['user_id'],'email_changed' if changed else 'email_verified','user',row['user_id']); db.commit(); self.send_json({'ok':True,'changed':changed}); return
                if path=='/api/account/verify-email/resend':
                    user=require_user(self,db)
                    if user.get('email_verified_at'): self.send_json({'ok':True,'already':True}); return
                    if FORGOT_LIMIT.hit(f"resend:{user['id']}"): self.send_json({'error':'Ya te hemos enviado varios correos. Espera unos minutos.'},429); return
                    send_email_verification(db,user['id']); db.commit(); self.send_json({'ok':True}); return
                if path=='/api/account/email':
                    # Change of email (Fase 5): confirmed from the NEW address before it is applied.
                    user=require_user(self,db); data=json_body(self); new=(clean_text(data.get('email'),160) or '').lower()
                    if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+',new) or not mail_deliverable(new): raise ValueError('Escribe un email válido.')
                    row=db.execute('SELECT password_hash FROM users WHERE id=?',(user['id'],)).fetchone()
                    if not verify_password(str(data.get('password') or ''),row['password_hash'] or ''): raise ValueError('La contraseña no es correcta.')
                    if db.execute('SELECT 1 FROM users WHERE lower(email)=? AND id<>?',(new,user['id'])).fetchone(): raise ValueError('Ese email ya lo usa otra cuenta.')
                    if FORGOT_LIMIT.hit(f"email-change:{user['id']}"): self.send_json({'error':'Demasiados intentos. Espera unos minutos.'},429); return
                    send_email_verification(db,user['id'],new); audit(db,user['id'],'email_change_requested','user',user['id']); db.commit(); self.send_json({'ok':True}); return
                if path=='/api/account/shares/revoke':
                    user=require_user(self,db); cid=int(json_body(self).get('center_id') or 0)
                    db.execute('UPDATE data_shares SET revoked_at=? WHERE user_id=? AND center_id=? AND revoked_at IS NULL',(now(),user['id'],cid))
                    audit(db,user['id'],'data_share_revoked','center',cid); db.commit(); self.send_json({'ok':True}); return
                if path=='/api/auth/logout':
                    self.logout_user(); return
                if path=='/api/provider/avatar':
                    user=require_user(self,db); require_role(user,{'center','freelance'}); fields,files=parse_multipart(self); file=files.get('file')
                    if not file: raise ValueError('Adjunta una imagen.')
                    public_url=save_public_image(file,f"provider_{user['id']}")
                    if user['role']=='center':
                        if not user['center_id']: raise ValueError('Tu cuenta no tiene centro asociado.')
                        db.execute("UPDATE centers SET logo_url=?,logo_source='uploaded',updated_at=? WHERE id=?",(public_url,now(),user['center_id']))
                    else:
                        db.execute('UPDATE users SET avatar_url=? WHERE id=?',(public_url,user['id']))
                    audit(db,user['id'],'provider_avatar_updated','center' if user['role']=='center' else 'user',user['center_id'] if user['role']=='center' else user['id']); db.commit(); self.send_json({'ok':True,'url':public_url}); return
                if path.startswith('/api/centers/') and path.endswith('/reviews'):
                    user=require_user(self,db)
                    parts=path.strip('/').split('/')
                    cid=int(parts[2]) if len(parts)>=4 and parts[2].isdigit() else 0
                    if not cid or not db.execute('SELECT 1 FROM centers WHERE id=? AND active=1',(cid,)).fetchone():
                        raise ValueError('Centro no válido.')
                    if user['role'] in {'center','admin'}:
                        raise PermissionError('Las cuentas profesionales y administrativas no pueden publicar reseñas de centros.')
                    data=json_body(self); rating=int(data.get('rating') or 0)
                    if rating<1 or rating>5: raise ValueError('La valoración debe estar entre 1 y 5 estrellas.')
                    title=clean_text(data.get('title'),120) or None
                    body=clean_text(data.get('body'),1200) or None
                    completed=db.execute("SELECT id FROM bookings WHERE center_id=? AND user_id=? AND status NOT IN ('cancelled','rejected') AND (payment_status='paid' OR status IN ('confirmed','completed')) ORDER BY booking_date DESC, id DESC LIMIT 1",(cid,user['id'])).fetchone()
                    if not completed: raise PermissionError('Podrás valorar este centro cuando tengas una reserva pagada o confirmada con él.')
                    existing=db.execute('SELECT id FROM center_reviews WHERE center_id=? AND user_id=?',(cid,user['id'])).fetchone()
                    if existing:
                        db.execute('UPDATE center_reviews SET rating=?,title=?,body=?,active=1,verified=1,updated_at=? WHERE id=?',(rating,title,body,now(),existing['id']))
                        rid=existing['id']; action='center_review_updated'
                    else:
                        cur=db.execute('INSERT INTO center_reviews(center_id,user_id,rating,title,body,active,verified,created_at,updated_at) VALUES(?,?,?,?,?,1,1,?,?)',(cid,user['id'],rating,title,body,now(),now()))
                        rid=cur.lastrowid; action='center_review_created'
                    audit(db,user['id'],action,'center_review',rid,{'center_id':cid,'rating':rating,'booking_id':completed['id']}); db.commit()
                    agg=db.execute('SELECT ROUND(AVG(rating),1) AS rating_average, COUNT(*) AS review_count FROM center_reviews WHERE center_id=? AND active=1',(cid,)).fetchone()
                    self.send_json({'ok':True,'id':rid,'rating_average':float(agg['rating_average'] or 0),'review_count':int(agg['review_count'] or 0)}); return
                if path=='/api/center-points/assign':
                    user=require_user(self,db); require_role(user,{'center','admin'}); data=json_body(self); center_id=user['center_id'] if user['role']=='center' else int(data.get('center_id') or 0); pid=int(data.get('dive_point_id') or 0)
                    if not center_id or not pid: raise ValueError('Centro y punto son obligatorios.')
                    if not db.execute('SELECT 1 FROM centers WHERE id=? AND active=1',(center_id,)).fetchone(): raise ValueError('Centro no válido.')
                    if not db.execute('SELECT 1 FROM dive_points WHERE id=? AND active=1',(pid,)).fetchone(): raise ValueError('Punto no válido.')
                    db.execute('INSERT OR IGNORE INTO center_point_links(center_id,dive_point_id,created_at) VALUES(?,?,?)',(center_id,pid,now())); audit(db,user['id'],'center_point_assigned','center_point',pid,{'center_id':center_id}); db.commit(); self.send_json({'ok':True}); return
                if path=='/api/center-points/unassign':
                    user=require_user(self,db); require_role(user,{'center','admin'}); data=json_body(self); center_id=user['center_id'] if user['role']=='center' else int(data.get('center_id') or 0); pid=int(data.get('dive_point_id') or 0)
                    if not center_id or not pid: raise ValueError('Centro y punto son obligatorios.')
                    db.execute('DELETE FROM center_point_links WHERE center_id=? AND dive_point_id=?',(center_id,pid)); audit(db,user['id'],'center_point_unassigned','center_point',pid,{'center_id':center_id}); db.commit(); self.send_json({'ok':True}); return
                if path=='/api/center-equipment':
                    user=require_user(self,db); require_role(user,{'center','admin'}); data=json_body(self); center_id=user['center_id'] if user['role']=='center' else int(data.get('center_id') or 0)
                    defaults={'fins':'Aletas','mask':'Máscara','wetsuit':'Traje de neopreno','regulator':'Regulador','bcd':'Chaleco BCD','tank':'Botella','computer':'Ordenador de buceo','full_kit':'Equipo completo'}
                    code=clean_text(data.get('code'),40); label=clean_text(data.get('label'),120) or defaults.get(code,code); price=data.get('price'); price=None if price in (None,'') else max(0,float(price))
                    if code not in defaults: raise ValueError('Equipo no válido.')
                    db.execute('''INSERT INTO center_equipment(center_id,code,label,price,active,sort_order,updated_at) VALUES(?,?,?,?,1,?,?) ON CONFLICT(center_id,code) DO UPDATE SET label=excluded.label,price=excluded.price,active=1,updated_at=excluded.updated_at''',(center_id,code,label,price,list(defaults).index(code),now())); db.commit(); self.send_json({'ok':True}); return
                if path=='/api/center/integration/regenerate':
                    user=require_user(self,db); require_role(user,{'center'}); cid=int(user['center_id'] or 0)
                    if not cid: raise ValueError('La cuenta aún no tiene un centro aprobado.')
                    key='wod_'+secrets.token_urlsafe(32); digest=hashlib.sha256(key.encode()).hexdigest(); prefix=key[:12]
                    if db.execute('SELECT id FROM center_integrations WHERE center_id=?',(cid,)).fetchone(): db.execute('UPDATE center_integrations SET api_key_hash=?,api_key_prefix=?,enabled=1,updated_at=? WHERE center_id=?',(digest,prefix,now(),cid))
                    else: db.execute('INSERT INTO center_integrations(center_id,api_key_hash,api_key_prefix,enabled,created_at,updated_at) VALUES(?,?,?,?,?,?)',(cid,digest,prefix,1,now(),now()))
                    audit(db,user['id'],'center_api_key_regenerated','center',cid); db.commit(); self.send_json({'ok':True,'api_key':key,'prefix':prefix}); return
                if path=='/api/center/integration/toggle':
                    user=require_user(self,db); require_role(user,{'center'}); cid=int(user['center_id'] or 0); data=json_body(self); enabled=1 if data.get('enabled',True) else 0
                    db.execute('UPDATE center_integrations SET enabled=?,updated_at=? WHERE center_id=?',(enabled,now(),cid)); audit(db,user['id'],'center_integration_toggled','center',cid,{'enabled':bool(enabled)}); db.commit(); self.send_json({'ok':True,'enabled':bool(enabled)}); return
                if path=='/api/integrations/bookings':
                    key=self.headers.get('X-WORLDIVES-API-Key','').strip(); data=json_body(self)
                    if not key: raise PermissionError('Falta la API Key de WORLDIVES.')
                    digest=hashlib.sha256(key.encode()).hexdigest(); integ=db.execute('SELECT * FROM center_integrations WHERE api_key_hash=? AND enabled=1',(digest,)).fetchone()
                    if not integ: raise PermissionError('API Key no válida o integración desactivada.')
                    cid=int(integ['center_id']); ext=clean_text(data.get('external_ref') or data.get('reservation_id'),180)
                    if ext:
                        old=db.execute('SELECT id,status FROM bookings WHERE center_id=? AND external_ref=?',(cid,ext)).fetchone()
                        if old: self.send_json({'ok':True,'duplicate':True,'booking_id':old['id'],'status':old['status']}); return
                    contact_email=(clean_text(data.get('email'),160) or '').lower() or None
                    contact_name=clean_text(data.get('fullname') or data.get('customer_name'),180) or 'Cliente web'
                    uid=find_or_create_customer(db,contact_name,contact_email,data.get('phone'),cid)
                    service_id=int(data.get('service_id') or 0) or None; slot_id=int(data.get('slot_id') or 0) or None; service=None
                    if service_id:
                        service=db.execute('SELECT * FROM provider_services WHERE id=? AND center_id=? AND active=1',(service_id,cid)).fetchone()
                        if not service: raise ValueError('Servicio no válido para este centro.')
                    participants=max(1,int(data.get('participants') or 1)); slot=None
                    if slot_id:
                        slot=db.execute("SELECT * FROM service_slots WHERE id=? AND service_id=? AND status IN ('open','full')",(slot_id,service_id)).fetchone()
                        if not slot or participants>slot['spots_available']: raise ValueError('La salida seleccionada no tiene plazas suficientes.')
                    bdate=slot['slot_date'] if slot else clean_text(data.get('booking_date'),20); btime=slot['slot_time'] if slot else clean_text(data.get('booking_time'),20)
                    if not bdate: raise ValueError('Falta booking_date.')
                    point_id=int(data.get('dive_point_id') or 0) or None; price=float(data.get('price') if data.get('price') not in (None,'') else (service['price'] if service else 0) or 0); status=clean_text(data.get('status'),30) or 'requested'; status='requested' if status in {'pending','requested'} else ('confirmed' if status=='confirmed' else 'requested'); reserved=0
                    if slot and status=='confirmed':
                        changed=db.execute("UPDATE service_slots SET spots_available=spots_available-?,status=CASE WHEN spots_available-?<=0 THEN 'full' ELSE 'open' END,updated_at=? WHERE id=? AND status='open' AND spots_available>=?",(participants,participants,now(),slot_id,participants)).rowcount
                        if changed!=1: raise ValueError('Las plazas acaban de cambiar.')
                        reserved=1
                    cur=db.execute('''INSERT INTO bookings(user_id,center_id,dive_point_id,service_id,slot_id,slot_reserved,booking_date,booking_time,participants,needs_equipment,equipment_items,equipment_notes,needs_guide,guide_notes,nitrox,pickup,notes,status,price,currency,payment_status,external_ref,source,contact_email,contact_name,contact_phone,public_token,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(uid,cid,point_id,service_id,slot_id,reserved,bdate,btime,participants,1 if data.get('needs_equipment') else 0,clean_text(data.get('equipment_items'),1000),clean_text(data.get('equipment_notes'),1000),1 if data.get('needs_guide') else 0,clean_text(data.get('guide_notes'),1000),1 if data.get('nitrox') else 0,1 if data.get('pickup') else 0,clean_text(data.get('notes'),2000),status,price,service['currency'] if service else 'EUR','paid' if data.get('paid') else ('at_center' if price>0 else 'not_required'),ext,'web',contact_email,contact_name,clean_text(data.get('phone'),60),wsec.random_token(),now(),now()))
                    audit(db,uid,'booking_imported','booking',cur.lastrowid,{'source':'center_web','external_ref':ext}); db.commit(); self.send_json({'ok':True,'booking_id':cur.lastrowid,'status':status,'external_ref':ext}); return
                if path=='/api/center/tariffs/save':
                    user=require_user(self,db); require_role(user,{'center'}); data=json_body(self); cid=int(user['center_id'] or 0); sid=int(data.get('service_id') or 0)
                    svc=db.execute('SELECT id,price,currency FROM provider_services WHERE id=? AND center_id=?',(sid,cid)).fetchone()
                    if not svc: raise ValueError('El servicio no pertenece a tu centro.')
                    price=max(0,float(data.get('price') or 0)); effective=clean_text(data.get('effective_from'),20) or now()[:10]
                    # Keep tariff history. A new tariff only replaces the price from its effective date.
                    db.execute('DELETE FROM center_tariffs WHERE center_id=? AND service_id=? AND effective_from=?',(cid,sid,effective))
                    db.execute('INSERT INTO center_tariffs(center_id,service_id,price,currency,effective_from,active,created_at,updated_at) VALUES(?,?,?,?,?,1,?,?)',(cid,sid,price,svc['currency'] or 'EUR',effective,now(),now()))
                    if effective <= now()[:10]:
                        db.execute('UPDATE provider_services SET price=?,updated_at=? WHERE id=?',(price,now(),sid))
                    audit(db,user['id'],'service_tariff_updated','provider_service',sid,{'price':price,'effective_from':effective}); db.commit(); self.send_json({'ok':True}); return
                if path=='/api/center/tariffs/history-delete':
                    user=require_user(self,db); require_role(user,{'center'}); data=json_body(self); tid=int(data.get('id') or 0); cid=int(user['center_id'] or 0)
                    row=db.execute('SELECT * FROM center_tariffs WHERE id=? AND center_id=?',(tid,cid)).fetchone()
                    if not row: raise ValueError('Tarifa no encontrada.')
                    db.execute('DELETE FROM center_tariffs WHERE id=?',(tid,)); db.commit(); self.send_json({'ok':True}); return
                if path=='/api/provider-services':
                    user=require_user(self,db); require_role(user,{'center','freelance'}); data=json_body(self)
                    center_id=user['center_id'] if user['role']=='center' else None
                    if user['role']=='center' and not center_id: raise ValueError('Tu cuenta de centro no tiene una ficha asociada.')
                    title=clean_text(data.get('title'),180)
                    if not title: raise ValueError('El nombre del servicio es obligatorio.')
                    price=max(0.0,float(data.get('price') or 0)); duration=int(data.get('duration_minutes') or 0) or None; maxp=int(data.get('max_participants') or 0) or None
                    stype=clean_text(data.get('service_type'),60) or 'inmersion'
                    if stype not in SERVICE_TYPES: stype='inmersion'
                    mode,resp_h,pay_h=clean_booking_mode(db,user,data,price)
                    color=clean_text(data.get('color'),20) or '#2563eb'
                    if not re.fullmatch(r'#[0-9a-fA-F]{6}',color): color='#2563eb'
                    currency=(clean_text(data.get('currency'),3) or 'EUR').upper()
                    if not re.fullmatch(r'[A-Z]{3}',currency): currency='EUR'
                    dep_kind,dep_value=clean_deposit(data,price); pol_h,pol_pct=clean_policy_numbers(data.get('cancel_free_hours'),data.get('cancel_refund_pct'))
                    if (pol_h is None)!=(pol_pct is None): raise ValueError('Indica las horas y el porcentaje de la política de cancelación del servicio, o deja los dos vacíos.')
                    cur=db.execute('''INSERT INTO provider_services(provider_user_id,center_id,service_type,title,description,duration_minutes,price,currency,max_participants,booking_mode,response_hours,payment_hours,active,color,deposit_type,deposit_value,cancel_free_hours,cancel_refund_pct,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,1,?,?,?,?,?,?,?)''',(user['id'],center_id,stype,title,clean_text(data.get('description'),5000),duration,price,currency,maxp,mode,resp_h,pay_h,color,dep_kind,dep_value,pol_h,pol_pct,now(),now()))
                    sid=cur.lastrowid
                    if center_id:
                        db.execute('INSERT INTO center_tariffs(center_id,service_id,price,currency,effective_from,active,created_at,updated_at) VALUES(?,?,?,?,?,1,?,?)',(center_id,sid,price,clean_text(data.get('currency'),3) or 'EUR',now()[:10],now(),now()))
                    sync_service_experience(db,user,sid,data)
                    audit(db,user['id'],'service_created','provider_service',sid); db.commit(); self.send_json({'ok':True,'id':sid}); return
                if path=='/api/provider-services/delete':
                    user=require_user(self,db); require_role(user,{'center','freelance'}); data=json_body(self); sid=int(data.get('id') or 0)
                    row=db.execute('SELECT provider_user_id,title FROM provider_services WHERE id=?',(sid,)).fetchone()
                    if not row or row['provider_user_id']!=user['id']: raise PermissionError('Este servicio no pertenece a tu cuenta.')
                    # Do not destroy a service that already has bookings: historical reservations must keep their context.
                    bookings_count=db.execute('SELECT COUNT(*) FROM bookings WHERE service_id=?',(sid,)).fetchone()[0]
                    if bookings_count:
                        raise ValueError('Este servicio ya tiene reservas asociadas y no se puede eliminar. Puedes desactivarlo para que deje de aparecer a nuevos clientes.')
                    db.execute('UPDATE travel_experiences SET active=0,service_id=NULL,updated_at=? WHERE service_id=?',(now(),sid))
                    db.execute('DELETE FROM provider_services WHERE id=?',(sid,))
                    audit(db,user['id'],'service_deleted','provider_service',sid,{'title':row['title']})
                    db.commit(); self.send_json({'ok':True,'id':sid}); return
                if path=='/api/provider-services/update':
                    user=require_user(self,db); require_role(user,{'center','freelance'}); data=json_body(self); sid=int(data.get('id') or 0)
                    row=db.execute('SELECT provider_user_id,center_id FROM provider_services WHERE id=?',(sid,)).fetchone()
                    if not row or row['provider_user_id']!=user['id']: raise PermissionError('Este servicio no pertenece a tu cuenta.')
                    duration=int(data.get('duration_minutes') or 0) or None; maxp=int(data.get('max_participants') or 0) or None
                    title=clean_text(data.get('title'),180)
                    if not title: raise ValueError('El nombre del servicio es obligatorio.')
                    stype=clean_text(data.get('service_type'),60) or 'inmersion'
                    if stype not in SERVICE_TYPES: stype='inmersion'
                    cur_price,_,_=effective_service_tariff(db,sid)
                    cur_svc=db.execute('SELECT booking_mode,response_hours,payment_hours FROM provider_services WHERE id=?',(sid,)).fetchone()
                    for k in ('booking_mode','response_hours','payment_hours'):
                        if data.get(k) in (None,''): data[k]=cur_svc[k]
                    if data.get('booking_mode')=='payment' and cur_svc['booking_mode']=='payment' and not service_payments_ready(db,{'center_id':row['center_id'],'provider_user_id':user['id']}):
                        data['booking_mode']='payment_keep'
                    # Changing the mode never touches bookings already in progress: each booking keeps its own mode.
                    mode,resp_h,pay_h=clean_booking_mode(db,user,data,cur_price)
                    color=clean_text(data.get('color'),20) or '#2563eb'
                    if not re.fullmatch(r'#[0-9a-fA-F]{6}',color): color='#2563eb'
                    db.execute('''UPDATE provider_services SET service_type=?,title=?,description=?,duration_minutes=?,max_participants=?,booking_mode=?,response_hours=?,payment_hours=?,active=?,color=?,updated_at=? WHERE id=?''',(stype,title,clean_text(data.get('description'),5000),duration,maxp,mode,resp_h,pay_h,1 if data.get('active',True) else 0,color,now(),sid))
                    if 'deposit_type' in data:
                        dep_kind,dep_value=clean_deposit(data,cur_price); db.execute('UPDATE provider_services SET deposit_type=?,deposit_value=? WHERE id=?',(dep_kind,dep_value,sid))
                    if 'cancel_free_hours' in data or 'cancel_refund_pct' in data:
                        pol_h,pol_pct=clean_policy_numbers(data.get('cancel_free_hours'),data.get('cancel_refund_pct'))
                        if (pol_h is None)!=(pol_pct is None): raise ValueError('Indica las horas y el porcentaje de la política de cancelación del servicio, o deja los dos vacíos.')
                        db.execute('UPDATE provider_services SET cancel_free_hours=?,cancel_refund_pct=? WHERE id=?',(pol_h,pol_pct,sid))
                    if 'publish_experience' in data: sync_service_experience(db,user,sid,data)
                    else: db.execute('UPDATE travel_experiences SET title=?,updated_at=? WHERE service_id=?',(clean_text(data.get('title'),180),now(),sid))
                    audit(db,user['id'],'service_updated','provider_service',sid); db.commit(); self.send_json({'ok':True}); return
                if path=='/api/provider-services/slot':
                    user=require_user(self,db); require_role(user,{'center','freelance'}); data=json_body(self); sid=int(data.get('service_id') or 0)
                    row=db.execute('SELECT provider_user_id FROM provider_services WHERE id=?',(sid,)).fetchone()
                    if not row or row['provider_user_id']!=user['id']: raise PermissionError('Este servicio no pertenece a tu cuenta.')
                    date=clean_text(data.get('slot_date'),20); tm=clean_text(data.get('slot_time'),10); total=max(1,int(data.get('spots_total') or 1))
                    if not date or not tm: raise ValueError('Indica fecha y hora de la salida.')
                    service=db.execute('SELECT center_id FROM provider_services WHERE id=?',(sid,)).fetchone()
                    point_ids=[int(x) for x in (data.get('dive_point_ids') or []) if str(x).isdigit()]
                    point_mode=clean_text(data.get('point_mode'),20) or 'fixed'
                    if point_mode not in ('fixed','weather'): point_mode='fixed'
                    if point_ids and (not service or not service['center_id']): raise ValueError('Esta salida no pertenece a un centro.')
                    if point_ids:
                        allowed={r['dive_point_id'] for r in db.execute('SELECT dive_point_id FROM center_point_links WHERE center_id=?',(service['center_id'],)).fetchall()}
                        if not set(point_ids).issubset(allowed): raise ValueError('Selecciona solo puntos asociados al centro.')
                    existing=db.execute('SELECT * FROM service_slots WHERE service_id=? AND slot_date=? AND slot_time=?',(sid,date,tm)).fetchone()
                    if existing:
                        consumed=int(existing['spots_total'])-int(existing['spots_available'])
                        if total < consumed: raise ValueError(f'No puedes bajar la capacidad a {total}: ya hay {consumed} plazas ocupadas.')
                        available=total-consumed; status='full' if available==0 else 'open'; slot_id=existing['id']
                        db.execute('UPDATE service_slots SET spots_total=?,spots_available=?,status=?,point_mode=?,updated_at=? WHERE id=?',(total,available,status,point_mode,now(),slot_id))
                    else:
                        available=total; slot_id=db.execute("INSERT INTO service_slots(service_id,slot_date,slot_time,spots_total,spots_available,status,point_mode,created_at,updated_at) VALUES(?,?,?,?,?,'open',?,?,?)",(sid,date,tm,total,total,point_mode,now(),now())).lastrowid
                    db.execute('DELETE FROM service_slot_points WHERE slot_id=?',(slot_id,))
                    db.executemany('INSERT OR IGNORE INTO service_slot_points(slot_id,dive_point_id) VALUES(?,?)',[(slot_id,pid) for pid in point_ids])
                    audit(db,user['id'],'service_slot_updated','service_slot',slot_id,{'spots_total':total,'spots_available':available,'dive_point_ids':point_ids}); db.commit(); self.send_json({'ok':True,'slot_id':slot_id,'spots_available':available}); return
                if path=='/api/provider-services/slot-update':
                    user=require_user(self,db); require_role(user,{'center','freelance'}); data=json_body(self); slot_id=int(data.get('id') or 0)
                    slot=db.execute('SELECT ss.*,s.provider_user_id FROM service_slots ss JOIN provider_services s ON s.id=ss.service_id WHERE ss.id=?',(slot_id,)).fetchone()
                    if not slot or slot['provider_user_id']!=user['id']: raise PermissionError('Esta salida no pertenece a tu cuenta.')
                    date=clean_text(data.get('slot_date'),20) or slot['slot_date']; tm=clean_text(data.get('slot_time'),10) or slot['slot_time']; total=max(1,int(data.get('spots_total') or slot['spots_total']))
                    consumed=int(slot['spots_total'])-int(slot['spots_available'])
                    if total < consumed: raise ValueError(f'No puedes bajar la capacidad a {total}: ya hay {consumed} plazas ocupadas.')
                    service=db.execute('SELECT center_id FROM provider_services WHERE id=?',(slot['service_id'],)).fetchone()
                    point_ids=[int(x) for x in (data.get('dive_point_ids') or []) if str(x).isdigit()]
                    point_mode=clean_text(data.get('point_mode'),20) or 'fixed'
                    if point_mode not in ('fixed','weather'): point_mode='fixed'
                    if point_ids and service and service['center_id']:
                        allowed={r['dive_point_id'] for r in db.execute('SELECT dive_point_id FROM center_point_links WHERE center_id=?',(service['center_id'],)).fetchall()}
                        if not set(point_ids).issubset(allowed): raise ValueError('Selecciona solo puntos asociados al centro.')
                    available=total-consumed; status='full' if available==0 else 'open'
                    db.execute('UPDATE service_slots SET slot_date=?,slot_time=?,spots_total=?,spots_available=?,status=?,point_mode=?,updated_at=? WHERE id=?',(date,tm,total,available,status,point_mode,now(),slot_id))
                    db.execute('DELETE FROM service_slot_points WHERE slot_id=?',(slot_id,)); db.executemany('INSERT OR IGNORE INTO service_slot_points(slot_id,dive_point_id) VALUES(?,?)',[(slot_id,pid) for pid in point_ids])
                    audit(db,user['id'],'service_slot_updated','service_slot',slot_id,{'spots_total':total,'spots_available':available,'dive_point_ids':point_ids}); db.commit(); self.send_json({'ok':True,'slot_id':slot_id,'spots_available':available}); return
                if path=='/api/provider-services/slot-delete':
                    user=require_user(self,db); require_role(user,{'center','freelance'}); data=json_body(self); slot_id=int(data.get('id') or 0)
                    slot=db.execute('SELECT ss.*,s.provider_user_id,s.title AS service_title FROM service_slots ss JOIN provider_services s ON s.id=ss.service_id WHERE ss.id=?',(slot_id,)).fetchone()
                    if not slot or slot['provider_user_id']!=user['id']: raise PermissionError('Esta salida no pertenece a tu cuenta.')
                    active=db.execute("SELECT COUNT(*) FROM bookings WHERE slot_id=? AND slot_reserved=1 AND status NOT IN ('cancelled','rejected')",(slot_id,)).fetchone()[0]
                    if active: raise ValueError('No puedes eliminar una salida que tiene reservas activas. Cancela o gestiona primero esas reservas.')
                    db.execute('DELETE FROM service_slot_points WHERE slot_id=?',(slot_id,))
                    db.execute('DELETE FROM service_slots WHERE id=?',(slot_id,))
                    audit(db,user['id'],'service_slot_deleted','service_slot',slot_id,{'service_id':slot['service_id'],'service_title':slot['service_title']})
                    db.commit(); self.send_json({'ok':True,'id':slot_id}); return
                if path=='/api/provider-services/slot-close':
                    user=require_user(self,db); require_role(user,{'center','freelance'}); data=json_body(self); slot_id=int(data.get('id') or 0)
                    slot=db.execute('SELECT ss.*,s.provider_user_id FROM service_slots ss JOIN provider_services s ON s.id=ss.service_id WHERE ss.id=?',(slot_id,)).fetchone()
                    if not slot or slot['provider_user_id']!=user['id']: raise PermissionError('Esta salida no pertenece a tu cuenta.')
                    active=db.execute("SELECT COUNT(*) FROM bookings WHERE slot_id=? AND slot_reserved=1 AND status NOT IN ('cancelled','rejected')",(slot_id,)).fetchone()[0]
                    if active: raise ValueError('No puedes cerrar una salida que todavía tiene reservas activas.')
                    db.execute("UPDATE service_slots SET status='closed',updated_at=? WHERE id=?",(now(),slot_id)); audit(db,user['id'],'service_slot_closed','service_slot',slot_id); db.commit(); self.send_json({'ok':True}); return
                if path=='/api/payments/checkout':
                    # Pay a booking (payment_in_progress within its hold, or accepted_pending_payment before its deadline)
                    # or an accepted travel experience. Everything else is refused.
                    user=require_user(self,db); data=json_body(self); booking_id=int(data.get('booking_id') or 0) or None; experience_booking_id=int(data.get('experience_booking_id') or 0) or None
                    if booking_id:
                        b0=db.execute('SELECT * FROM bookings WHERE id=? AND user_id=?',(booking_id,user['id'])).fetchone()
                        if not b0: raise PermissionError('Reserva no válida.')
                        pay=start_checkout(db,user,b0)
                    elif experience_booking_id:
                        eb=db.execute('SELECT * FROM experience_bookings WHERE id=? AND user_id=?',(experience_booking_id,user['id'])).fetchone()
                        if not eb: raise PermissionError('Solicitud de experiencia no válida.')
                        pay=start_experience_checkout(db,user,eb)
                    else: raise ValueError('Indica la reserva que quieres pagar.')
                    self.send_json(dict(pay,ok=True)); return
                if path=='/api/payments/cancel':
                    user=require_user(self,db); bid=int(json_body(self).get('booking_id') or 0)
                    order=db.execute("SELECT * FROM payment_orders WHERE booking_id=? AND user_id=? AND status='pending' ORDER BY id DESC LIMIT 1",(bid,user['id'])).fetchone()
                    if not order: self.send_json({'ok':True,'released':False}); return
                    if stripe_secret() and order['provider_payment_id']:
                        try:
                            sess=stripe_session(order)
                            if _obj(sess,'payment_status') in ('paid','no_payment_required'):
                                finalize_paid_order(db,order,sess,'cancel-check'); db.commit(); self.send_json({'ok':True,'paid':True}); return
                            if _obj(sess,'status')=='open': expire_checkout(order)
                        except Exception as exc: sys.stderr.write(f'[pagos] cancelar pedido {order["id"]}: {exc}\n')
                    release_order_hold(db,order,'cancelled'); audit(db,user['id'],'payment_cancelled','payment_order',order['id']); db.commit()
                    b_=booking_row(db,bid)
                    self.send_json({'ok':True,'released':True,'status':b_['status'] if b_ else None}); return
                if path=='/api/payments':
                    # G12: the diver only gets what he needs about his own payments (no fees, connected accounts or checkout links).
                    user=require_user(self,db); rows=db.execute('''SELECT po.id,po.booking_id,po.experience_booking_id,po.amount,po.currency,po.status,po.created_at,po.paid_at,po.amount_received,
                                                                          po.receipt_url,po.card_brand,po.card_last4,po.refund_amount,po.refunded_at,po.refunded_total,po.payment_kind,s.title AS service_title,COALESCE(c.name,pu.fullname) AS center_name
                                                                     FROM payment_orders po LEFT JOIN provider_services s ON s.id=po.service_id LEFT JOIN centers c ON c.id=s.center_id LEFT JOIN users pu ON pu.id=po.provider_user_id WHERE po.user_id=? ORDER BY po.id DESC''',(user['id'],)).fetchall()
                    self.send_json({'items':[dict(x,reference=f"PAY-{x['id']:05d}") for x in rows]}); return

                if path=='/api/account/profile':
                    user=require_user(self,db); data=json_body(self)
                    db.execute('''INSERT INTO user_profiles(
                        user_id,phone,country,city,preferred_language,certification_id,notes,date_of_birth,
                        emergency_contact_name,emergency_contact_phone,equipment_required,suit_type,suit_size,
                        boot_size,bcd_size,fin_size,mask_size,usual_weight_kg,tank_preference,
                        computer_preference,equipment_notes,updated_at
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    ON CONFLICT(user_id) DO UPDATE SET
                        phone=excluded.phone,country=excluded.country,city=excluded.city,
                        preferred_language=excluded.preferred_language,certification_id=excluded.certification_id,
                        notes=excluded.notes,date_of_birth=excluded.date_of_birth,
                        emergency_contact_name=excluded.emergency_contact_name,
                        emergency_contact_phone=excluded.emergency_contact_phone,
                        equipment_required=excluded.equipment_required,suit_type=excluded.suit_type,
                        suit_size=excluded.suit_size,boot_size=excluded.boot_size,bcd_size=excluded.bcd_size,
                        fin_size=excluded.fin_size,mask_size=excluded.mask_size,usual_weight_kg=excluded.usual_weight_kg,
                        tank_preference=excluded.tank_preference,computer_preference=excluded.computer_preference,
                        equipment_notes=excluded.equipment_notes,updated_at=excluded.updated_at''',
                    (user['id'],clean_text(data.get('phone'),50),clean_text(data.get('country'),100),
                     clean_text(data.get('city'),100),normalize_lang(clean_text(data.get('preferred_language'),10) or 'es'),
                     int(data['certification_id']) if data.get('certification_id') else None,
                     clean_text(data.get('notes'),2000),clean_text(data.get('date_of_birth'),20),
                     clean_text(data.get('emergency_contact_name'),160),clean_text(data.get('emergency_contact_phone'),60),
                     1 if data.get('equipment_required') else 0,clean_text(data.get('suit_type'),80),
                     clean_text(data.get('suit_size'),40),clean_text(data.get('boot_size'),40),
                     clean_text(data.get('bcd_size'),40),clean_text(data.get('fin_size'),40),
                     clean_text(data.get('mask_size'),40),
                     float(data.get('usual_weight_kg')) if data.get('usual_weight_kg') not in (None,'') else None,
                     clean_text(data.get('tank_preference'),120),clean_text(data.get('computer_preference'),120),
                     clean_text(data.get('equipment_notes'),2000),now()))
                    audit(db,user['id'],'profile_updated','user',user['id']); sync_user_rewards(db,user['id']); db.commit(); self.send_json({'ok':True}); return
                if path=='/api/account/documents':
                    user=require_user(self,db); fields,files=parse_multipart(self); file=files.get('file')
                    if not file: raise ValueError('Adjunta un archivo PDF o imagen.')
                    dtype=clean_document_type(fields.get('document_type'))
                    expires=clean_date(fields.get('expires_at'))
                    if db.execute('SELECT COUNT(*) FROM user_documents WHERE user_id=?',(user['id'],)).fetchone()[0]>=MAX_DOCUMENTS_PER_USER: raise ValueError(f'Puedes guardar como máximo {MAX_DOCUMENTS_PER_USER} documentos. Elimina alguno para subir otro.')
                    original=re.sub(r'[\x00-\x1f/\\\\]+','_',Path(file['filename'] or 'documento').name)[:160]
                    p=save_upload(user['id'],file,'doc'); did=db.execute('INSERT INTO user_documents(user_id,document_type,title,file_path,original_name,expires_at,status,uploaded_at) VALUES(?,?,?,?,?,?,?,?)',(user['id'],dtype,clean_text(fields.get('title'),160) or original,p,original,expires,'valid' if expires else 'uploaded',now())).lastrowid
                    audit(db,user['id'],'document_uploaded','user_document',did,{'type':dtype}); sync_user_rewards(db,user['id']); db.commit(); self.send_json({'ok':True,'id':did}); return
                if path=='/api/account/documents/delete':
                    user=require_user(self,db); data=json_body(self); did=int(data['id']); doc=db.execute('SELECT * FROM user_documents WHERE id=? AND user_id=?',(did,user['id'])).fetchone();
                    if not doc: self.send_json({'error':'Documento no encontrado'},404); return
                    db.execute('DELETE FROM user_documents WHERE id=?',(did,)); audit(db,user['id'],'document_deleted','user_document',did); db.commit()
                    delete_document_file(doc['file_path']); self.send_json({'ok':True}); return
                if path=='/api/messages':
                    # G11: WORLDIVES is not a social network. There is no free messaging between users: a centre or a
                    # freelance can only send a NOTICE about one of ITS bookings (e.g. a change of time). The diver gets it
                    # by email and in «Avisos», with the centre's phone and email; there is no reply through the platform.
                    user=require_user(self,db); require_role(user,{'center','freelance'}); data=json_body(self)
                    booking_id=int(data.get('booking_id') or 0) or None; experience_booking_id=int(data.get('experience_booking_id') or 0) or None
                    if bool(booking_id)==bool(experience_booking_id): raise ValueError('Los avisos siempre van ligados a una reserva concreta.')
                    recipient_id=booking_notice_recipient(db,user,booking_id,experience_booking_id)
                    subject=clean_text(data.get('subject'),180) or 'Aviso sobre tu reserva'; body=clean_text(data.get('body'),3000) or ''
                    if len(body)<5: raise ValueError('Escribe el aviso.')
                    if NOTICE_LIMIT.hit(f"notice:{user['id']}"): raise ValueError('Has enviado demasiados avisos en la última hora.')
                    mid=send_booking_notice(db,user,recipient_id,booking_id,experience_booking_id,subject,body)
                    audit(db,user['id'],'booking_notice_sent','message',mid,{'booking_id':booking_id,'experience_booking_id':experience_booking_id}); db.commit(); self.send_json({'ok':True,'id':mid}); return
                if path=='/api/messages/read':
                    user=require_user(self,db); data=json_body(self); mid=int(data.get('id') or 0); row=db.execute('SELECT id FROM messages WHERE id=? AND recipient_user_id=?',(mid,user['id'])).fetchone();
                    if not row: self.send_json({'error':'Mensaje no encontrado'},404); return
                    db.execute('UPDATE messages SET read_at=? WHERE id=?',(now(),mid)); db.commit(); self.send_json({'ok':True}); return
                if path=='/api/auth/forgot':
                    data=json_body(self); email=(clean_text(data.get('email'),160) or '').strip().lower()
                    if FORGOT_LIMIT.hit(f'forgot:{self.client_ip()}') or (email and FORGOT_LIMIT.hit(f'forgot-mail:{email}')): self.send_json({'error':'Demasiadas solicitudes. Espera unos minutos.'},429); return
                    u=db.execute("SELECT id FROM users WHERE (lower(email)=? OR lower(username)=?) AND password_hash<>'!'",(email,email)).fetchone() if email else None
                    if u:
                        token=new_password_reset(db,u['id'])
                        notify_user(db,u['id'],'password_reset',{'reset_url':f'{public_site_url()}/#/restablecer?token={token}'},('user',u['id']))
                        audit(db,u['id'],'password_reset_requested','user',u['id'])
                    db.commit()
                    # Same answer whether the account exists or not (no account enumeration).
                    self.send_json({'ok':True}); return
                if path=='/api/auth/reset':
                    data=json_body(self); token=str(data.get('token') or '')[:200]; new=str(data.get('password') or '')
                    if FORGOT_LIMIT.hit(f'reset:{self.client_ip()}'): self.send_json({'error':'Demasiados intentos. Espera unos minutos.'},429); return
                    check_new_password(new)
                    th=hashlib.sha256(token.encode()).hexdigest()
                    r=db.execute('SELECT * FROM password_resets WHERE token_hash=?',(th,)).fetchone()
                    if not r or r['used_at'] or r['expires_at']<now(): raise ValueError('El enlace no es válido o ha caducado. Pide uno nuevo.')
                    if db.execute('UPDATE password_resets SET used_at=? WHERE token_hash=? AND used_at IS NULL',(now(),th)).rowcount!=1: raise ValueError('El enlace ya se ha utilizado.')
                    db.execute('UPDATE users SET password_hash=? WHERE id=?',(hash_password(new),r['user_id']))
                    db.execute('DELETE FROM sessions WHERE user_id=?',(r['user_id'],))
                    notify_user(db,r['user_id'],'password_changed',{'when':datetime.now().strftime('%d/%m/%Y %H:%M')},('user',r['user_id']))
                    audit(db,r['user_id'],'password_reset_done','user',r['user_id']); db.commit(); self.send_json({'ok':True}); return
                if path=='/api/account/language':
                    user=require_user(self,db); lang=clean_text(json_body(self).get('lang'),5) or 'es'
                    lang=normalize_lang(lang)
                    db.execute('INSERT INTO user_profiles(user_id,preferred_language,updated_at) VALUES(?,?,?) ON CONFLICT(user_id) DO UPDATE SET preferred_language=excluded.preferred_language',(user['id'],lang,now()))
                    db.commit(); self.send_json({'ok':True}); return
                if path=='/api/account/accept-terms':
                    user=require_user(self,db); kind=json_body(self).get('kind')
                    if kind=='pro': require_role(user,{'center','freelance','admin'}); db.execute('UPDATE users SET pro_terms_version=?,pro_terms_accepted_at=? WHERE id=?',(LEGAL_VERSION,now(),user['id']))
                    else: db.execute('UPDATE users SET terms_version=?,terms_accepted_at=? WHERE id=?',(LEGAL_VERSION,now(),user['id']))
                    audit(db,user['id'],'terms_accepted','user',user['id'],{'kind':kind or 'user','version':LEGAL_VERSION}); db.commit(); self.send_json({'ok':True,'version':LEGAL_VERSION}); return
                if path=='/api/account/delete':
                    user=require_user(self,db); data=json_body(self)
                    if user['role']!='recreational': raise PermissionError('Las cuentas de centro, profesional o administración se dan de baja escribiéndonos: así no se pierden reservas de clientes.')
                    row=db.execute('SELECT password_hash FROM users WHERE id=?',(user['id'],)).fetchone()
                    if not verify_password(str(data.get('password') or ''),row['password_hash'] or ''): raise ValueError('La contraseña no es correcta.')
                    delete_user_account(db,user); db.commit(); self.logout_user(); return
                if path.startswith('/api/bookings/') and path.endswith('/cancel'):
                    user=require_user(self,db); bid=int(path.split('/')[-2]); data=json_body(self)
                    b=db.execute('SELECT * FROM bookings WHERE id=? AND user_id=?',(bid,user['id'])).fetchone()
                    if not b: self.send_json({'error':'Reserva no encontrada'},404); return
                    if wbk.normalize_state(b['status'])=='payment_in_progress':
                        # Abandoning the payment of a «Pago al reservar» booking: nothing was charged, the spots are freed.
                        for o in db.execute("SELECT * FROM payment_orders WHERE booking_id=? AND status='pending'",(bid,)).fetchall(): release_order_hold(db,o,'cancelled')
                        if wbk.normalize_state(booking_row(db,bid)['status'])=='payment_in_progress': expire_booking(db,booking_row(db,bid),'payment_cancelled',notify=False)
                        db.commit(); self.send_json({'ok':True,'refund':'none_paid','refund_amount':0}); return
                    if wbk.normalize_state(b['status']) not in wbk.CANCELLABLE: raise ValueError('Esta reserva ya no se puede cancelar.')
                    terms=booking_cancel_terms(db,b)
                    if terms['started']: raise ValueError('La actividad ya ha empezado o ha pasado: habla directamente con el centro.')
                    if data.get('preview'): self.send_json({'ok':True,'terms':terms}); return
                    if db.execute("SELECT 1 FROM payment_orders WHERE booking_id=? AND status='pending'",(bid,)).fetchone():
                        for o in db.execute("SELECT * FROM payment_orders WHERE booking_id=? AND status='pending'",(bid,)).fetchall(): release_order_hold(db,o,'cancelled')
                        b=db.execute('SELECT * FROM bookings WHERE id=?',(bid,)).fetchone()
                    if db.execute("UPDATE bookings SET status='cancelled',cancelled_at=?,cancelled_by='diver',updated_at=? WHERE id=? AND status IN ('pending','requested','accepted_pending_payment','confirmed')",(now(),now(),bid)).rowcount!=1: raise ValueError('Esta reserva ya no se puede cancelar.')
                    release_booking_spots(db,b)
                    outcome='none_paid'
                    if terms['paid_online']:
                        # Fase 2.4: the provider manages its refunds. The amount of its policy is proposed to it (and reminded after 72 h).
                        propose_refund(db,b,terms['refund_amount'],'diver_cancel')
                        outcome='proposed' if terms['refund_amount']>0 else 'no_refund'
                    reason=clean_text(data.get('reason'),300)
                    if reason: db.execute('UPDATE bookings SET internal_notes=COALESCE(internal_notes||char(10),\'\')||? WHERE id=?',('Motivo de la cancelación: '+reason,bid))
                    notify_booking(db,bid,'cancelled_diver',{'refund':outcome})
                    audit(db,user['id'],'booking_cancelled_by_diver','booking',bid,{'refund':outcome,'amount':terms['refund_amount']}); db.commit()
                    self.send_json({'ok':True,'refund':outcome,'refund_amount':terms['refund_amount']}); return
                if path in ('/api/center/cancellation-policy','/api/provider/cancellation-policy'):
                    # Fase 2.6: free cancellation until X hours before, then Y % refunded. The three old presets still work.
                    user=require_user(self,db); require_role(user,{'center','freelance'}); data=json_body(self); pol=data.get('policy')
                    if pol in CANCEL_POLICIES: hours,pct=CANCEL_POLICIES[pol],0
                    else:
                        hours,pct=clean_policy_numbers(data.get('cancel_free_hours'),data.get('cancel_refund_pct'))
                        if hours is None or pct is None: raise ValueError('Elige una política de cancelación.')
                        pol='custom'
                    note=clean_text(data.get('note'),500) or None
                    if user['role']=='center':
                        if not user['center_id']: raise ValueError('Tu cuenta no tiene un centro asociado.')
                        db.execute('UPDATE centers SET cancellation_policy=?,cancel_free_hours=?,cancel_refund_pct=?,cancellation_note=?,updated_at=? WHERE id=?',(pol,hours,pct,note,now(),user['center_id']))
                        target=('center',user['center_id'])
                    else:
                        db.execute('UPDATE users SET cancel_free_hours=?,cancel_refund_pct=?,cancellation_note=? WHERE id=?',(hours,pct,note,user['id'])); target=('user',user['id'])
                    audit(db,user['id'],'cancellation_policy_updated',target[0],target[1],{'hours':hours,'pct':pct}); db.commit(); DIRECTORY.invalidate()
                    self.send_json({'ok':True,'cancel_free_hours':hours,'cancel_refund_pct':pct,'text':policy_text(hours,pct)}); return
                if path=='/api/provider/payment-profile':
                    # Fiscal data of the provider for the booking voucher («Prestador del servicio»).
                    user=require_user(self,db); require_role(user,{'center','freelance'}); data=json_body(self)
                    vals=(clean_text(data.get('legal_name'),160),clean_text(data.get('tax_id'),40),clean_text(data.get('fiscal_address'),300))
                    if vals[1] and not re.fullmatch(r'[A-Za-z0-9 .\-/]{4,40}',vals[1]): raise ValueError('El NIF / número fiscal no parece válido.')
                    if user['role']=='center':
                        if not user['center_id']: raise ValueError('Tu cuenta no tiene un centro asociado.')
                        db.execute('UPDATE centers SET legal_name=?,tax_id=?,fiscal_address=?,updated_at=? WHERE id=?',vals+(now(),user['center_id']))
                    else: db.execute('UPDATE users SET legal_name=?,tax_id=?,fiscal_address=? WHERE id=?',vals+(user['id'],))
                    audit(db,user['id'],'provider_fiscal_data_updated'); db.commit(); self.send_json({'ok':True}); return
                if path.startswith('/api/bookings/') and path.endswith('/refund'):
                    # Fase 2.4: the provider refunds part or all of what the diver paid online, from its own Stripe account.
                    user=require_user(self,db); require_role(user,{'center','freelance'}); bid=int(path.split('/')[-2]); data=json_body(self)
                    b=booking_row(db,bid)
                    if not b: self.send_json({'error':'Reserva no encontrada'},404); return
                    require_booking_provider(user,b)
                    try: amount=round(float(str(data.get('amount') or '0').replace(',','.')),2)
                    except ValueError: raise ValueError('Indica el importe que quieres devolver.')
                    paid_,refunded_,orders_=booking_paid_online(db,bid)
                    if not orders_: raise ValueError('Esta reserva no tiene pagos online que devolver.')
                    note=clean_text(data.get('note'),300) or ''
                    if amount<=0 or amount>round(paid_-refunded_,2)+0.005: raise ValueError(f'Puedes devolver entre 0,01 y {paid_-refunded_:.2f} {b["currency"] or "EUR"}.')
                    left=amount
                    for o in reversed(orders_):
                        o=db.execute('SELECT * FROM payment_orders WHERE id=?',(o['id'],)).fetchone()
                        avail=round(float(o['amount_received'] or o['amount'] or 0)-float(o['refunded_total'] or 0),2)
                        if avail<=0 or left<=0: continue
                        part=min(avail,left); refund_payment(db,o,part,'requested_by_customer',user['id'],note,'panel'); left=round(left-part,2)
                    notify_booking(db,bid,'refund_issued',{'amount':amount,'note':note})
                    db.commit(); b=booking_row(db,bid)
                    self.send_json({'ok':True,'refunded_total':b['refunded_total'],'payment_status':b['payment_status'],'status':b['status']}); return
                if path=='/api/admin/payments/incident':
                    # The administrator does not move money: it only sees payments and refunds and marks incidents.
                    user=require_user(self,db); require_role(user,{'admin'}); data=json_body(self); oid=int(data.get('order_id') or 0)
                    kind=clean_text(data.get('incident'),30) or None
                    if kind not in (None,'refund_pending','dispute','dispute_closed','customer_complaint','resolved'): raise ValueError('Tipo de incidencia no válido.')
                    if not db.execute('UPDATE payment_orders SET incident=?,incident_note=?,incident_at=?,incident_by=?,updated_at=? WHERE id=?',(kind,clean_text(data.get('note'),500),now(),user['id'],now(),oid)).rowcount: raise ValueError('Pago no encontrado.')
                    audit(db,user['id'],'payment_incident_marked','payment_order',oid,{'incident':kind}); db.commit(); self.send_json({'ok':True}); return
                if path=='/api/reports':
                    data=json_body(self); ip=self.client_ip()
                    if report_rate_limited(ip): self.send_json({'error':'Has enviado muchas denuncias seguidas. Inténtalo más tarde.'},429); return
                    reason=data.get('reason'); details=clean_text(data.get('details'),3000) or ''
                    if reason not in REPORT_REASONS: raise ValueError('Elige el motivo de la denuncia.')
                    if len(details)<20: raise ValueError('Explica con un poco más de detalle qué ocurre (mínimo 20 caracteres).')
                    cu=current_user(self,db)
                    name=clean_text(data.get('name'),120) or (cu['fullname'] if cu else ''); email=(clean_text(data.get('email'),160) or (cu['email'] if cu else '') or '').lower()
                    target=clean_text(data.get('target_url'),500) or ''
                    if not data.get('good_faith'): raise ValueError('Confirma que la información es exacta y que la envías de buena fe.')
                    rid=db.execute('INSERT INTO content_reports(reason,target_url,details,reporter_name,reporter_email,user_id,ip_hash,status,created_at) VALUES(?,?,?,?,?,?,?,?,?)',
                                   (reason,target,details,name,email,cu['id'] if cu else None,wsec.ip_hash(ip),'open',now())).lastrowid
                    notify_admins(db,'admin_content_report',{'reason':REPORT_REASONS[reason],'target':target or '—','details':details,'reporter':' · '.join(x for x in (name,email) if x) or 'Anónimo'},('report',rid))
                    if mail_deliverable(email):
                        queue_email(db,'report_received',email,name,{'first_name':(name or '').split(' ')[0],'ref':f'DEN-{rid:05d}','reason':mail_t('es',REPORT_REASONS[reason])},'es',('report',rid))
                    audit(db,cu['id'] if cu else None,'content_reported','content_report',rid,{'reason':reason}); db.commit(); self.send_json({'ok':True,'id':rid,'ref':f'DEN-{rid:05d}'}); return
                if path=='/api/admin/reports/resolve':
                    user=require_user(self,db); require_role(user,{'admin'}); data=json_body(self); rid=int(data.get('id') or 0); st=data.get('status')
                    if st not in ('open','actioned','dismissed'): raise ValueError('Estado no válido.')
                    if not db.execute('UPDATE content_reports SET status=?,resolution=?,resolved_by=?,resolved_at=? WHERE id=?',(st,clean_text(data.get('resolution'),2000),user['id'],now() if st!='open' else None,rid)).rowcount: raise ValueError('Denuncia no encontrada.')
                    r=db.execute('SELECT * FROM content_reports WHERE id=?',(rid,)).fetchone()
                    if st!='open' and mail_deliverable(r['reporter_email']):
                        queue_email(db,'report_resolved',r['reporter_email'],r['reporter_name'],{'first_name':(r['reporter_name'] or '').split(' ')[0],'ref':f'DEN-{rid:05d}',
                                    'decision':'Hemos retirado o corregido el contenido denunciado.' if st=='actioned' else 'Tras revisarlo, no hemos encontrado motivos para retirar el contenido.',
                                    'resolution':clean_text(data.get('resolution'),2000) or ''},'es',('report',rid))
                    audit(db,user['id'],'content_report_'+st,'content_report',rid); db.commit(); self.send_json({'ok':True}); return
                if path=='/api/admin/legal':
                    user=require_user(self,db); require_role(user,{'admin'}); data=json_body(self)
                    for k in LEGAL_FIELDS:
                        if k in data:
                            v=(clean_text(data.get(k),300) or '').strip()
                            if k=='email' and v and not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+',v): raise ValueError('El email de contacto no es válido.')
                            db.execute('INSERT INTO site_settings(key,value,updated_at,updated_by) VALUES(?,?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at,updated_by=excluded.updated_by',('legal_'+k,v,now(),user['id']))
                    audit(db,user['id'],'legal_settings_updated','site_settings',None,'legal'); db.commit(); self.send_json({'ok':True}); return
                if path=='/api/admin/emails/test':
                    user=require_user(self,db); require_role(user,{'admin'}); to=(clean_text(json_body(self).get('to'),160) or user['email'] or '').strip()
                    if not mail_deliverable(to): raise ValueError('Escribe un email real para la prueba.')
                    queue_email(db,'test',to,user['fullname'],{},'es',('user',user['id'])); db.commit()
                    cfg=smtp_config()
                    if not cfg['enabled']: self.send_json({'ok':True,'sent':False,'message':'El correo está en la cola. Se enviará cuando configures el servidor SMTP (WOD_SMTP_HOST).'}); return
                    row=db.execute("SELECT * FROM email_outbox WHERE template='test' AND to_email=? ORDER BY id DESC LIMIT 1",(to.lower(),)).fetchone()
                    try:
                        send_one_email(cfg,row); db.execute("UPDATE email_outbox SET status='sent',sent_at=?,attempts=attempts+1 WHERE id=?",(now(),row['id'])); db.commit()
                        self.send_json({'ok':True,'sent':True,'message':f'Enviado a {to}. Revisa la bandeja de entrada (y la de spam).'}); return
                    except Exception as exc:
                        db.execute("UPDATE email_outbox SET status='failed',attempts=attempts+1,last_error=? WHERE id=?",(str(exc)[:300],row['id'])); db.commit()
                        raise ValueError(f'El servidor de correo ha rechazado el envío: {exc}')
                if path=='/api/admin/emails/resend':
                    user=require_user(self,db); require_role(user,{'admin'}); eid=int(json_body(self).get('id') or 0)
                    r=db.execute('SELECT * FROM email_outbox WHERE id=?',(eid,)).fetchone()
                    if not r: raise ValueError('Correo no encontrado.')
                    if not mail_deliverable(r['to_email']): raise ValueError('Este destinatario no tiene un email real.')
                    db.execute("INSERT INTO email_outbox(template,lang,to_email,to_name,subject,html,text,status,related_type,related_id,attempts,created_at) VALUES(?,?,?,?,?,?,?,'queued',?,?,0,?)",
                               (r['template'],r['lang'],r['to_email'],r['to_name'],r['subject'],r['html'],r['text'],r['related_type'],r['related_id'],now()))
                    audit(db,user['id'],'email_resent','email_outbox',eid); db.commit(); self.send_json({'ok':True}); return
                if path=='/api/bookings':
                    user=require_user(self,db); data=json_body(self)
                    center_id=int(data.get('center_id') or 0) or None
                    point_id=int(data.get('dive_point_id') or 0) or None
                    if point_id and not db.execute('SELECT 1 FROM dive_points WHERE id=? AND active=1',(point_id,)).fetchone(): raise ValueError('Punto de buceo no válido.')
                    service_id=int(data.get('service_id') or 0) or None
                    service=None; provider_user_id=None
                    if service_id and not center_id:
                        # Fase 2.7: services of a freelance professional without a centre.
                        service=db.execute("SELECT s.* FROM provider_services s JOIN users u ON u.id=s.provider_user_id WHERE s.id=? AND s.active=1 AND s.center_id IS NULL AND u.role='freelance'",(service_id,)).fetchone()
                        if not service: raise ValueError('Servicio no válido.')
                        provider_user_id=service['provider_user_id']
                    else:
                        if not center_id or not db.execute('SELECT 1 FROM centers WHERE id=? AND active=1',(center_id,)).fetchone(): raise ValueError('Centro no válido.')
                        if service_id:
                            service=db.execute('SELECT * FROM provider_services WHERE id=? AND active=1 AND center_id=?',(service_id,center_id)).fetchone()
                            if not service: raise ValueError('Servicio no válido para este centro.')
                            provider_user_id=service['provider_user_id']
                    participants=max(1,int(data.get('participants') or 1))
                    if service and service['max_participants'] and participants>int(service['max_participants']): raise ValueError(f'Este servicio admite como máximo {service["max_participants"]} participantes por reserva.')
                    slot_id=int(data.get('slot_id') or 0) or None
                    slot=None
                    if slot_id:
                        slot=db.execute("SELECT * FROM service_slots WHERE id=? AND service_id=? AND status IN ('open','full')",(slot_id,service_id)).fetchone()
                        if not slot: raise ValueError('La salida seleccionada ya no está disponible.')
                        if participants>slot['spots_available']: raise ValueError(f'Solo quedan {slot["spots_available"]} plazas disponibles.')
                        slot_points=[int(r['dive_point_id']) for r in db.execute('SELECT dive_point_id FROM service_slot_points WHERE slot_id=?',(slot_id,)).fetchall()]
                        if slot_points:
                            # La selección visible del usuario es la fuente de verdad, pero
                            # aceptamos también el nombre como respaldo por si el select oculto
                            # no se sincroniza en algún navegador/cache. Nunca elegimos un punto
                            # arbitrario cuando la salida tiene varios.
                            point_name=(clean_text(data.get('dive_point_name'),200) or '').strip().casefold()
                            if point_id and point_id not in slot_points:
                                point_id=None
                            if not point_id and point_name:
                                matches=[]
                                for rr in db.execute('SELECT id,name FROM dive_points WHERE id IN (%s)' % ','.join('?'*len(slot_points)), slot_points).fetchall():
                                    if (clean_text(rr['name'],200) or '').strip().casefold()==point_name:
                                        matches.append(int(rr['id']))
                                if len(matches)==1: point_id=matches[0]
                            if not point_id and len(slot_points)==1: point_id=slot_points[0]
                            # Una salida puede tener varios puntos (por ejemplo, un servicio
                            # de doble inmersion). La reserva sigue necesitando un punto
                            # principal para el logbook y la ficha de reserva. Si el cliente no
                            # ha podido transmitir la seleccion visual, usamos de forma
                            # determinista el primer punto programado en la salida en lugar de
                            # bloquear una reserva valida. Si el cliente eligio uno, siempre se
                            # respeta esa eleccion.
                            if not point_id and len(slot_points)>1: point_id=slot_points[0]
                    if slot:
                        # La salida seleccionada es la fuente de verdad para fecha/hora.
                        data['booking_date']=slot['slot_date']; data['booking_time']=slot['slot_time']
                    bdate=clean_text(data.get('booking_date'),20) or (slot['slot_date'] if slot else None)
                    if not bdate or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',bdate): raise ValueError('Elige la fecha de la actividad.')
                    btime=clean_text(data.get('booking_time'),20)
                    start=wbk.activity_start(bdate,btime)
                    if start and start<=local_now(): raise ValueError('Esa salida ya ha empezado o ha pasado. Elige otra fecha.')
                    price, service_currency, price_lines = booking_quote(db, center_id, service, participants, bdate, as_list(data.get('extra_ids')), as_list(data.get('equipment_codes')))
                    mode='payment' if service and service['booking_mode']=='payment' else 'request'
                    ready=service_payments_ready(db,service) if service else False
                    deadline=None; hold=None; slot_reserved=0
                    payee=payee_of(db,center_id,provider_user_id)
                    pol=provider_policy(payee,service)  # the policy shown before paying is the one that applies
                    deposit=deposit_for(service,price,participants)
                    if mode=='payment':
                        # «Pago al reservar»: the diver pays to book. Never silently turned into «pay at the centre».
                        if not ready: raise ValueError('Este servicio se reserva pagando online y ahora mismo el centro no tiene los cobros activos. Prueba más tarde o contacta con el centro.')
                        if price<=0:
                            status='confirmed'; payment_status='not_required'
                        else:
                            status='payment_in_progress'; payment_status='pending'; hold=local_iso(local_now()+_timedelta(minutes=HOLD_MINUTES))
                        if slot:
                            if not reserve_slot_spots(db,slot['id'],participants): raise ValueError('Las plazas acaban de cambiar. Vuelve a seleccionar la salida.')
                            slot_reserved=1
                    else:
                        # «Bajo petición»: no money and no spots until the centre accepts, within its response deadline.
                        status='requested'; payment_status='not_required' if price<=0 else ('required' if ready else 'at_center')
                        hours=wbk.clamp_hours(service['response_hours'] if service else None, wbk.DEFAULT_RESPONSE_HOURS)
                        deadline=local_iso(wbk.deadline_before_start(local_now(),hours,start))
                    cur=db.execute('''INSERT INTO bookings(user_id,center_id,provider_user_id,dive_point_id,service_id,slot_id,slot_reserved,booking_date,booking_time,participants,needs_equipment,equipment_items,equipment_notes,needs_guide,guide_notes,nitrox,pickup,notes,status,price,currency,payment_status,booking_mode,response_deadline,hold_expires_at,confirmed_at,terms_version,price_breakdown,deposit_amount,amount_paid,amount_due,cancel_free_hours,cancel_refund_pct,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0,?,?,?,?,?)''',
                                   (user['id'],center_id,provider_user_id,point_id,service_id,slot_id,slot_reserved,bdate,btime,participants,1 if data.get('needs_equipment') else 0,clean_text(data.get('equipment_items'),1000),clean_text(data.get('equipment_notes'),1000),1 if data.get('needs_guide') else 0,clean_text(data.get('guide_notes'),1000),1 if data.get('nitrox') else 0,1 if data.get('pickup') else 0,clean_text(data.get('notes'),2000),
                                    status,price,service['currency'] if service else 'EUR',payment_status,mode,deadline,hold,now() if status=='confirmed' else None,legal_doc_version(db,'reservas'),json.dumps(price_lines,ensure_ascii=False),
                                    deposit,price,pol['free_hours'],pol['refund_pct'],now(),now()))
                    bid=cur.lastrowid
                    audit(db,user['id'],'booking_created','booking',bid,{'mode':mode,'status':status})
                    if status=='payment_in_progress':
                        # The booking is not visible to the centre until Stripe confirms the payment.
                        db.commit()
                        try:
                            pay=start_checkout(db,user,booking_row(db,bid))
                        except ValueError:
                            expire_booking(db,booking_row(db,bid),'checkout_failed',notify=False); db.commit(); raise
                        self.send_json({'ok':True,'id':bid,'status':status,'payment_required':True,'checkout_url':pay['checkout_url'],'hold_expires_at':hold,'price':price,'deposit':deposit,'currency':service_currency,'booking_mode':mode}); return
                    notify_booking(db,bid,'created')
                    db.commit(); self.send_json({'ok':True,'id':bid,'status':status,'payment_required':False,'price':price,'currency':service_currency,'booking_mode':mode,'response_deadline':deadline}); return
                if path.startswith('/api/bookings/') and path.endswith('/status'):
                    # Provider decisions on a booking (Fase 1B): accept / reject a request (optional reason), cancel, complete.
                    user=require_user(self,db); require_role(user,{'admin','center','freelance'}); bid=int(path.split('/')[-2]); data=json_body(self); status=clean_text(data.get('status'),30)
                    if status=='accepted': status='confirmed'
                    if status not in {'confirmed','rejected','completed','cancelled'}: raise ValueError('Estado no válido.')
                    row=booking_row(db,bid)
                    if not row: self.send_json({'error':'Reserva no encontrada'},404); return
                    require_booking_provider(user,row)
                    cur_state=wbk.normalize_state(row['status'])
                    if status==cur_state: self.send_json({'ok':True,'unchanged':True,'status':cur_state}); return
                    result={'ok':True}
                    if status=='confirmed':
                        if cur_state=='requested': result['status']=accept_booking(db,user,row)
                        elif cur_state=='accepted_pending_payment': raise ValueError('Esta reserva espera el pago online del buceador. Si te paga en el centro, registra el cobro desde «Cobro».')
                        elif cur_state=='payment_in_progress': raise ValueError('El buceador está pagando ahora mismo. La reserva se confirmará sola cuando Stripe confirme el pago.')
                        else: raise ValueError('Esta reserva no se puede confirmar en su estado actual.')
                    elif status=='rejected':
                        result['refund']=reject_booking(db,user,row,data.get('reason') or ''); result['status']='rejected'
                    elif status=='cancelled':
                        if cur_state not in ('confirmed','accepted_pending_payment'): raise ValueError('Solo se pueden cancelar reservas aceptadas o confirmadas. Las solicitudes se rechazan.')
                        release_booking_spots(db,row)
                        db.execute("UPDATE bookings SET status='cancelled',cancelled_at=?,cancelled_by='center',reject_reason=?,updated_at=? WHERE id=?",(now(),clean_text(data.get('reason'),500) or None,now(),bid))
                        for o in db.execute("SELECT * FROM payment_orders WHERE booking_id=? AND status='pending'",(bid,)).fetchall():
                            expire_checkout(o); db.execute("UPDATE payment_orders SET status='cancelled',updated_at=? WHERE id=?",(now(),o['id']))
                        # The provider cancels: everything paid is refunded unless it sets a smaller amount (it is told the law).
                        paid_,refunded_,_o=booking_paid_online(db,bid); net_=round(paid_-refunded_,2)
                        amt=data.get('refund_amount'); amt=net_ if amt in (None,'') else max(0.0,min(net_,round(float(str(amt).replace(',','.')),2)))
                        result['refund']=refund_booking(db,bid,amt,'requested_by_customer',user['id'],clean_text(data.get('reason'),300) or 'Cancelada por el centro','center_cancel') if amt>0 else ('no_refund' if net_>0 else 'none_paid')
                        if result['refund']=='refunded': notify_booking(db,bid,'refund_issued',{'amount':amt,'note':clean_text(data.get('reason'),300) or ''})
                        notify_booking(db,bid,'cancelled_center',{'refund':result['refund'],'reason':clean_text(data.get('reason'),500) or ''})
                        result['status']='cancelled'
                    elif status=='completed':
                        if cur_state!='confirmed': raise ValueError('Solo se puede completar una reserva confirmada.')
                        if str(row['booking_date'] or '')>local_now().date().isoformat(): raise ValueError('Solo puedes marcar como completada una reserva cuya fecha ya ha llegado.')
                        db.execute("UPDATE bookings SET status='completed',updated_at=? WHERE id=?",(now(),bid))
                        b=db.execute('''SELECT b.id,b.user_id,b.booking_date,COALESCE(c.name,pu.fullname) AS center_name,p.name AS point_name,p.country,p.dive_type
                                       FROM bookings b LEFT JOIN centers c ON c.id=b.center_id LEFT JOIN users pu ON pu.id=b.provider_user_id LEFT JOIN dive_points p ON p.id=b.dive_point_id WHERE b.id=?''',(bid,)).fetchone()
                        if b and not is_guest_user(db,b['user_id']) and not db.execute('SELECT 1 FROM logbook_entries WHERE booking_id=?',(bid,)).fetchone():
                            site=b['point_name'] or b['center_name']
                            note=f"Inmersión generada automáticamente desde la reserva #{bid} · {b['center_name']}"
                            db.execute('INSERT INTO logbook_entries(user_id,dive_date,site,country,depth,duration,dive_type,notes,created_at,booking_id) VALUES(?,?,?,?,?,?,?,?,?,?)',(b['user_id'],b['booking_date'],site,b['country'],None,None,b['dive_type'] or 'Buceo recreativo',note,now(),bid))
                        sync_user_rewards(db,row['user_id']); result['status']='completed'
                    audit(db,user['id'],'booking_status_changed','booking',bid,{'from':cur_state,'to':result.get('status',status),'reason':clean_text(data.get('reason'),200) or None})
                    db.commit(); self.send_json(result); return
                if path=='/api/logbook':
                    user=require_user(self,db); data=json_body(self)
                    v=clean_logbook(data)
                    cur=db.execute('INSERT INTO logbook_entries(user_id,dive_date,site,country,depth,duration,dive_type,notes,created_at) VALUES(?,?,?,?,?,?,?,?,?)',(user['id'],v['dive_date'],v['site'],v['country'],v['depth'],v['duration'],v['dive_type'],v['notes'],now())); audit(db,user['id'],'logbook_created','logbook',cur.lastrowid); db.commit(); self.send_json({'ok':True,'id':cur.lastrowid}); return
                if path=='/api/logbook/update':
                    user=require_user(self,db); data=json_body(self); lid=int(data.get('id') or 0); v=clean_logbook(data)
                    row=db.execute('SELECT booking_id FROM logbook_entries WHERE id=? AND user_id=?',(lid,user['id'])).fetchone()
                    if not row: self.send_json({'error':'Inmersión no encontrada'},404); return
                    db.execute('UPDATE logbook_entries SET dive_date=?,site=?,country=?,depth=?,duration=?,dive_type=?,notes=? WHERE id=?',(v['dive_date'],v['site'],v['country'],v['depth'],v['duration'],v['dive_type'],v['notes'],lid))
                    audit(db,user['id'],'logbook_updated','logbook',lid); db.commit(); self.send_json({'ok':True}); return
                if path=='/api/logbook/delete':
                    user=require_user(self,db); lid=int(json_body(self).get('id') or 0)
                    row=db.execute('SELECT booking_id FROM logbook_entries WHERE id=? AND user_id=?',(lid,user['id'])).fetchone()
                    if not row: self.send_json({'error':'Inmersión no encontrada'},404); return
                    if row['booking_id']: raise ValueError('Esta inmersión viene de una reserva completada: puedes editarla, pero no borrarla.')
                    db.execute('DELETE FROM logbook_entries WHERE id=?',(lid,)); audit(db,user['id'],'logbook_deleted','logbook',lid); db.commit(); self.send_json({'ok':True}); return
                if path=='/api/account/password':
                    user=require_user(self,db); data=json_body(self); new=str(data.get('new_password') or '')
                    row=db.execute('SELECT password_hash FROM users WHERE id=?',(user['id'],)).fetchone()
                    if not verify_password(str(data.get('current_password') or ''),row['password_hash'] or ''): raise ValueError('La contraseña actual no es correcta.')
                    check_new_password(new)
                    db.execute('UPDATE users SET password_hash=? WHERE id=?',(hash_password(new),user['id']))
                    tok=''
                    for item in self.headers.get('Cookie','').split(';'):
                        k,_,v_=item.strip().partition('=')
                        if k==COOKIE: tok=v_
                    db.execute('DELETE FROM sessions WHERE user_id=? AND token_hash<>?',(user['id'],hashlib.sha256(tok.encode()).hexdigest()))
                    notify_user(db,user['id'],'password_changed',{'when':datetime.now().strftime('%d/%m/%Y %H:%M')},('user',user['id']))
                    audit(db,user['id'],'password_changed','user',user['id']); db.commit(); self.send_json({'ok':True}); return
                if path=='/api/account/identity':
                    user=require_user(self,db); name=clean_text(json_body(self).get('fullname'),120)
                    if not name or len(name)<2: raise ValueError('Escribe tu nombre y apellidos.')
                    db.execute('UPDATE users SET fullname=? WHERE id=?',(name,user['id'])); audit(db,user['id'],'identity_updated','user',user['id']); db.commit(); self.send_json({'ok':True}); return
                if path=='/api/provider/profile':
                    user=require_user(self,db); require_role(user,{'freelance','center'}); data=json_body(self)
                    db.execute('UPDATE users SET provider_bio=?,instagram_url=?,facebook_url=?,twitter_url=?,youtube_url=?,tiktok_url=? WHERE id=?',(clean_text(data.get('provider_bio'),3000),clean_url_field(data.get('instagram_url')),clean_url_field(data.get('facebook_url')),clean_url_field(data.get('twitter_url')),clean_url_field(data.get('youtube_url')),clean_url_field(data.get('tiktok_url')),user['id']))
                    if user['role']=='center' and user['center_id']:
                        db.execute('UPDATE centers SET instagram_url=?,facebook_url=?,twitter_url=?,youtube_url=?,tiktok_url=?,updated_at=? WHERE id=?',(clean_url_field(data.get('instagram_url')),clean_url_field(data.get('facebook_url')),clean_url_field(data.get('twitter_url')),clean_url_field(data.get('youtube_url')),clean_url_field(data.get('tiktok_url')),now(),user['center_id']))
                    audit(db,user['id'],'provider_profile_updated','user',user['id']); db.commit(); self.send_json({'ok':True}); return
                if path=='/api/provider/center-update':
                    user=require_user(self,db); require_role(user,{'center'}); data=json_body(self); cid=int(user['center_id'] or 0)
                    if not cid: raise ValueError('Tu cuenta no está asociada a un centro verificado.')
                    current=db.execute('SELECT latitude,longitude,logo_url FROM centers WHERE id=?',(cid,)).fetchone()
                    if not clean_text(data.get('name'),180): raise ValueError('El nombre del centro es obligatorio.')
                    # Keep the map position unless the form explicitly sends a new one.
                    lat=float(data['latitude']) if data.get('latitude') not in (None,'') else current['latitude']
                    lng=float(data['longitude']) if data.get('longitude') not in (None,'') else current['longitude']
                    db.execute('''UPDATE centers SET name=?,country=?,region=?,city=?,address=?,website=?,phone=?,email=?,description=?,specialties=?,latitude=?,longitude=?,logo_url=?,instagram_url=?,facebook_url=?,twitter_url=?,youtube_url=?,tiktok_url=?,logo_source='provider_uploaded',updated_at=? WHERE id=?''',(clean_text(data.get('name'),180),clean_text(data.get('country'),100),clean_text(data.get('region'),120),clean_text(data.get('city'),100),clean_text(data.get('address'),250),clean_url_field(data.get('website'),250),clean_text(data.get('phone'),60),clean_text(data.get('email'),160),clean_text(data.get('description'),5000),clean_text(data.get('specialties'),2000),lat,lng,wsec.clean_local_or_http_url(data.get('logo_url'),500) if 'logo_url' in data else current['logo_url'],clean_url_field(data.get('instagram_url')),clean_url_field(data.get('facebook_url')),clean_url_field(data.get('twitter_url')),clean_url_field(data.get('youtube_url')),clean_url_field(data.get('tiktok_url')),now(),cid))
                    audit(db,user['id'],'center_profile_updated','center',cid); db.commit(); self.send_json({'ok':True}); return
                if path=='/api/provider/center-create':
                    user=require_user(self,db)
                    if user['role'] not in {'center','freelance','recreational'} and user.get('requested_role')!='center': raise PermissionError('Cuenta no autorizada para solicitar un centro.')
                    if user['center_id']: raise ValueError('Tu cuenta ya está asociada a un centro.')
                    data=json_body(self); phone=clean_text(data.get('phone'),60); name=clean_text(data.get('name'),180)
                    if not name or not phone: raise ValueError('Nombre y teléfono del centro son obligatorios.')
                    if db.execute("SELECT 1 FROM center_claims WHERE user_id=? AND status='pending'",(user['id'],)).fetchone(): raise ValueError('Ya tienes una solicitud pendiente de verificación.')
                    pro_signup_check(db,data)
                    website=wsec.clean_http_url(data.get('website'),250) if data.get('website') else None
                    # Always a new centre, hidden until the administrator verifies the request (G2).
                    cur=db.execute('''INSERT INTO centers(name,country,region,city,address,website,phone,email,description,specialties,latitude,longitude,active,created_at,updated_at,verification_status,data_confidence,source_name) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,0,?,?,?,?,?)''',(unique_center_name(db,name,clean_text(data.get('city'),100)),clean_text(data.get('country'),100) or 'España',clean_text(data.get('region'),120),clean_text(data.get('city'),100),clean_text(data.get('address'),250),website,phone,clean_text(data.get('email'),160),clean_text(data.get('description'),5000),clean_text(data.get('specialties'),2000),clean_lat(data.get('latitude')),clean_lng(data.get('longitude')),now(),now(),'pending_provider','provider_submitted','WORLDIVES DISCOVERY provider'))
                    cid=cur.lastrowid
                    db.execute('INSERT INTO center_claims(user_id,center_id,requested_center_name,phone,city,website,note,status,created_at,requested_role,email) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(user['id'],cid,name,phone,clean_text(data.get('city'),100),website,clean_text(data.get('note'),2000),'pending',now(),'center',user['email']))
                    db.execute("UPDATE users SET requested_role='center' WHERE id=?",(user['id'],))
                    audit(db,user['id'],'center_created_by_provider','center',cid); db.commit(); self.send_json({'ok':True,'id':cid,'status':'pending'}); return
                if path=='/api/dive-points':
                    user=require_user(self,db); require_role(user,{'admin','center'}); data=json_body(self)
                    center_id=data.get('center_id') or (user['center_id'] if user['role']=='center' else None)
                    if user['role']=='center' and center_id!=user['center_id']: raise PermissionError('Solo puedes crear puntos de tu centro.')
                    cur=db.execute('''INSERT INTO dive_points(name,country,region,dive_type,latitude,longitude,difficulty,min_depth,max_depth,description,access_info,center_id,verification_status,created_by_user_id,updated_by_user_id,active,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(clean_text(data.get('name'),180),clean_text(data.get('country'),100),clean_text(data.get('region'),120),clean_text(data.get('dive_type'),100),float(data.get('latitude')),float(data.get('longitude')),clean_text(data.get('difficulty'),50),data.get('min_depth') or None,data.get('max_depth') or None,clean_text(data.get('description'),5000),clean_text(data.get('access_info'),3000),center_id,'verified' if user['role']=='admin' else 'pending_center',user['id'],user['id'],1,now(),now())); audit(db,user['id'],'dive_point_created','dive_point',cur.lastrowid); db.commit(); self.send_json({'ok':True,'id':cur.lastrowid}); return
                if path.startswith('/api/dive-points/') and path.endswith('/virtual/upload'):
                    user=require_user(self,db); require_role(user,{'admin','center'}); pid=int(path.split('/')[3])
                    can_manage_virtual(db,user,pid)
                    fields,files=parse_multipart(self); file=files.get('file')
                    v=clean_virtual_payload(fields,has_file=bool(file))
                    media_path=save_virtual_media(file,pid,v['type']) if file else None
                    cur=db.execute('INSERT INTO virtual_experiences(dive_point_id,title,experience_type,provider,url,media_path,description,duration_seconds,active,created_by_user_id,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(pid,v['title'],v['type'],v['provider'],v['url'],media_path,v['description'],v['duration'],1,user['id'],now(),now()))
                    audit(db,user['id'],'virtual_experience_created','virtual_experience',cur.lastrowid); db.commit(); self.send_json({'ok':True,'id':cur.lastrowid,'media_path':media_path}); return
                if path.startswith('/api/dive-points/') and path.endswith('/virtual'):
                    user=require_user(self,db); require_role(user,{'admin','center'}); pid=int(path.split('/')[3])
                    can_manage_virtual(db,user,pid)
                    v=clean_virtual_payload(json_body(self))
                    cur=db.execute('INSERT INTO virtual_experiences(dive_point_id,title,experience_type,provider,url,media_path,description,duration_seconds,active,created_by_user_id,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(pid,v['title'],v['type'],v['provider'],v['url'],None,v['description'],v['duration'],1,user['id'],now(),now()))
                    audit(db,user['id'],'virtual_experience_created','virtual_experience',cur.lastrowid); db.commit(); self.send_json({'ok':True,'id':cur.lastrowid}); return
                if path.startswith('/api/dive-points/') and path.endswith('/photos/delete'):
                    user=require_user(self,db); pid=int(path.split('/')[3]); data=json_body(self); phid=int(data.get('photo_id') or 0)
                    ph=db.execute('SELECT * FROM dive_point_photos WHERE id=? AND dive_point_id=?',(phid,pid)).fetchone()
                    if not ph: self.send_json({'error':'Foto no encontrada'},404); return
                    if not point_photo_allowed(db,user,pid) or (user['role']!='admin' and ph['uploaded_by']!=user['id']): raise PermissionError('Solo puedes quitar las fotos que has subido tú.')
                    db.execute('DELETE FROM dive_point_photos WHERE id=?',(phid,)); audit(db,user['id'],'dive_point_photo_deleted','dive_point',pid); db.commit()
                    delete_public_image(ph['image_path']); self.send_json({'ok':True}); return
                if path.startswith('/api/dive-points/') and path.endswith('/photos'):
                    user=require_user(self,db); pid=int(path.split('/')[3])
                    if not db.execute('SELECT 1 FROM dive_points WHERE id=? AND active=1',(pid,)).fetchone(): self.send_json({'error':'Punto no encontrado'},404); return
                    if not point_photo_allowed(db,user,pid): raise PermissionError('Solo el administrador o un centro que bucea en este punto puede subir fotos.')
                    if db.execute('SELECT COUNT(*) FROM dive_point_photos WHERE dive_point_id=?',(pid,)).fetchone()[0]>=24: raise ValueError('Este punto ya tiene 24 fotos. Quita alguna para añadir otra.')
                    fields,files=parse_multipart(self)
                    url=save_public_image(files.get('file'),f'point_{pid}')
                    cur=db.execute('INSERT INTO dive_point_photos(dive_point_id,image_path,caption,sort_order,uploaded_by) VALUES(?,?,?,?,?)',(pid,url,clean_text(fields.get('caption'),300),db.execute('SELECT COALESCE(MAX(sort_order),0)+1 FROM dive_point_photos WHERE dive_point_id=?',(pid,)).fetchone()[0],user['id']))
                    audit(db,user['id'],'dive_point_photo_added','dive_point',pid); db.commit()
                    self.send_json({'ok':True,'id':cur.lastrowid,'url':url}); return
                if path=='/api/admin/site-promos':
                    user=require_user(self,db); require_role(user,{'admin'}); fields,files=parse_multipart(self)
                    pid=int(fields.get('id') or 0); kind=fields.get('kind') or 'partner'
                    if kind not in PROMO_KINDS: raise ValueError('Tipo no válido.')
                    title=clean_text(fields.get('title'),120)
                    if not title: raise ValueError('Indica el nombre.')
                    row=db.execute('SELECT * FROM site_promos WHERE id=?',(pid,)).fetchone() if pid else None
                    if pid and not row: self.send_json({'error':'No encontrado'},404); return
                    def _d(v):
                        v=(clean_text(v,10) or '').strip()
                        if v and not re.fullmatch(r'\d{4}-\d{2}-\d{2}',v): raise ValueError('Fecha no válida.')
                        return v or None
                    starts,ends=_d(fields.get('starts_on')),_d(fields.get('ends_on'))
                    if starts and ends and ends<starts: raise ValueError('La fecha de fin es anterior a la de inicio.')
                    # Fase 2.10: the label «Patrocinado» is fixed (not editable) and every sponsor is recorded.
                    sponsor=clean_text(fields.get('sponsor_name'),160) or (row['title'] if row and kind=='partner' else None) or (title if kind=='partner' else None)
                    if not sponsor: raise ValueError('Indica quién patrocina (empresa o persona que paga la publicación).')
                    try: amount=round(float(str(fields.get('sponsor_amount') or '').replace(',','.')),2) if str(fields.get('sponsor_amount') or '').strip() else None
                    except ValueError: raise ValueError('El importe del patrocinio debe ser un número.')
                    old=row['image_path'] if row else None; img=old
                    if files.get('file'): img=save_public_image(files.get('file'),'promo')
                    elif fields.get('remove_image')=='1': img=None
                    vals=(kind,title,clean_text(fields.get('subtitle'),240) or '',SPONSORED_LABEL,clean_promo_url(fields.get('url')),img,starts,ends,
                          int(fields.get('sort_order') or 0),0 if fields.get('active')=='0' else 1,now())
                    if row: db.execute('UPDATE site_promos SET kind=?,title=?,subtitle=?,label=?,url=?,image_path=?,starts_on=?,ends_on=?,sort_order=?,active=?,updated_at=? WHERE id=?',(*vals,pid))
                    else: pid=db.execute('INSERT INTO site_promos(kind,title,subtitle,label,url,image_path,starts_on,ends_on,sort_order,active,updated_at,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(*vals,now())).lastrowid
                    placement='band' if kind=='partner' else 'offer'
                    cur_sp=db.execute('SELECT * FROM sponsorships WHERE placement=? AND ref_id=? AND ended_at IS NULL ORDER BY id DESC LIMIT 1',(placement,pid)).fetchone()
                    sp_vals=(sponsor,clean_text(fields.get('sponsor_contact'),200),starts,ends,amount,(clean_text(fields.get('sponsor_currency'),3) or 'EUR').upper(),clean_text(fields.get('sponsor_notes'),500))
                    if cur_sp and cur_sp['sponsor_name']==sponsor:
                        db.execute('UPDATE sponsorships SET sponsor_name=?,sponsor_contact=?,starts_on=?,ends_on=?,amount=?,currency=?,notes=? WHERE id=?',(*sp_vals,cur_sp['id']))
                    else:
                        if cur_sp: db.execute('UPDATE sponsorships SET ended_at=? WHERE id=?',(now(),cur_sp['id']))
                        db.execute('INSERT INTO sponsorships(placement,ref_id,sponsor_name,sponsor_contact,starts_on,ends_on,amount,currency,notes,created_by,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(placement,pid,*sp_vals,user['id'],now()))
                    audit(db,user['id'],'site_promo_saved','site_promo',pid,{'sponsor':sponsor}); db.commit()
                    if old and old!=img: delete_public_image(old)
                    self.send_json({'ok':True,'id':pid}); return
                if path=='/api/admin/site-promos/settings':
                    user=require_user(self,db); require_role(user,{'admin'}); data=json_body(self)
                    email=(clean_text(data.get('partners_email'),160) or '').strip()
                    if email and not re.fullmatch(r'[^@\s<>"]+@[^@\s<>"]+\.[^@\s<>"]+',email): raise ValueError('Revisa el email de contacto.')
                    text=(clean_text(data.get('partners_text'),200) or '').strip()
                    for k,v in (('partners_email',email),('partners_text',text)):
                        db.execute('INSERT INTO site_settings(key,value,updated_at,updated_by) VALUES(?,?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at,updated_by=excluded.updated_by',(k,v,now(),user['id']))
                    audit(db,user['id'],'site_settings_updated','site_settings',None,'partners'); db.commit(); self.send_json({'ok':True}); return
                if path=='/api/admin/site-promos/delete':
                    user=require_user(self,db); require_role(user,{'admin'}); data=json_body(self); pid=int(data.get('id') or 0)
                    row=db.execute('SELECT image_path FROM site_promos WHERE id=?',(pid,)).fetchone()
                    if not row: self.send_json({'error':'No encontrado'},404); return
                    db.execute('DELETE FROM site_promos WHERE id=?',(pid,))
                    db.execute("UPDATE sponsorships SET ended_at=? WHERE ref_id=? AND placement IN ('band','offer') AND ended_at IS NULL",(now(),pid))  # the register keeps the history
                    audit(db,user['id'],'site_promo_deleted','site_promo',pid); db.commit()
                    delete_public_image(row['image_path']); self.send_json({'ok':True}); return
                if path=='/api/center/promotions':
                    user=require_user(self,db); require_role(user,{'center'}); cid=user['center_id']; data=json_body(self); pid=int(data.get('id') or 0)
                    if not cid: raise ValueError('La cuenta aún no tiene un centro aprobado.')
                    title=clean_text(data.get('title'),120)
                    if not title: raise ValueError('Ponle un título a la promoción.')
                    vu=clean_text(data.get('valid_until'),10) or ''; vf=clean_text(data.get('valid_from'),10) or None
                    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',vu): raise ValueError('Indica hasta qué día es válida la promoción.')
                    if vf and not re.fullmatch(r'\d{4}-\d{2}-\d{2}',vf): vf=None
                    if vf and vf>vu: raise ValueError('La fecha de inicio no puede ser posterior a la de caducidad.')
                    if not pid and vu<_dt.date.today().isoformat(): raise ValueError('La fecha de caducidad ya ha pasado.')
                    uses=max(1,min(50,int(data.get('uses_per_code') or 1)))
                    vals=(title,clean_text(data.get('description'),1000) or '',clean_text(data.get('value_text'),120) or '',clean_text(data.get('conditions'),1000) or '',vf,vu,uses)
                    if pid:
                        if not db.execute('SELECT 1 FROM promotions WHERE id=? AND center_id=?',(pid,cid)).fetchone(): raise PermissionError('Esta promoción no es de tu centro.')
                        db.execute('UPDATE promotions SET title=?,description=?,value_text=?,conditions=?,valid_from=?,valid_until=?,uses_per_code=?,updated_at=? WHERE id=?',vals+(now(),pid))
                    else:
                        pid=db.execute('INSERT INTO promotions(center_id,created_by,title,description,value_text,conditions,valid_from,valid_until,uses_per_code,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(cid,user['id'])+vals+('active',now(),now())).lastrowid
                    want={int(x) for x in (data.get('partner_ids') or []) if str(x).isdigit() and int(x)!=cid}
                    have={r['center_id'] for r in db.execute('SELECT center_id FROM promotion_partners WHERE promotion_id=?',(pid,)).fetchall()}
                    for c in want-have:
                        if db.execute('SELECT 1 FROM centers WHERE id=? AND active=1',(c,)).fetchone():
                            db.execute("INSERT INTO promotion_partners(promotion_id,center_id,status,updated_at) VALUES(?,?,'invited',?)",(pid,c,now()))
                            issuer=db.execute('SELECT name FROM centers WHERE id=?',(cid,)).fetchone()['name']
                            for _em,_nm,_lg in center_recipients(db,c):
                                queue_email(db,'center_promo_invite',_em,_nm,{'issuer':issuer,'promo_title':title,'panel_qr_url':public_site_url()+'/#/admin?tab=qr'},_lg,('promotion',pid))
                    for c in have-want: db.execute('DELETE FROM promotion_partners WHERE promotion_id=? AND center_id=?',(pid,c))
                    audit(db,user['id'],'promotion_saved','promotion',pid); db.commit(); self.send_json({'ok':True,'id':pid}); return
                if path.startswith('/api/center/promotions/') and path.endswith('/status'):
                    user=require_user(self,db); require_role(user,{'center'}); pid=int(path.split('/')[4]); st=json_body(self).get('status')
                    if st not in ('active','archived'): raise ValueError('Estado no válido.')
                    if not db.execute('UPDATE promotions SET status=?,updated_at=? WHERE id=? AND center_id=?',(st,now(),pid,user['center_id'])).rowcount: raise PermissionError('Esta promoción no es de tu centro.')
                    audit(db,user['id'],'promotion_'+st,'promotion',pid); db.commit(); self.send_json({'ok':True}); return
                if path.startswith('/api/center/promotions/') and path.endswith('/assign'):
                    user=require_user(self,db); require_role(user,{'center'}); pid=int(path.split('/')[4]); data=json_body(self); cid=user['center_id']
                    pr=db.execute('SELECT * FROM promotions WHERE id=? AND center_id=?',(pid,cid)).fetchone()
                    if not pr: self.send_json({'error':'Promoción no encontrada'},404); return
                    if pr['status']!='active' or pr['valid_until']<_dt.date.today().isoformat(): raise ValueError('Esta promoción ya no está activa.')
                    ids=[int(x) for x in (data.get('user_ids') or []) if str(x).isdigit()][:500]
                    if not ids: raise ValueError('Elige al menos un cliente.')
                    created=skipped=0; cname=db.execute('SELECT name FROM centers WHERE id=?',(cid,)).fetchone()['name']
                    for uid in ids:
                        if not is_center_client(db,cid,uid): skipped+=1; continue
                        if db.execute("SELECT 1 FROM promotion_codes WHERE promotion_id=? AND user_id=? AND status='active'",(pid,uid)).fetchone(): skipped+=1; continue
                        code=new_promo_code(db)
                        db.execute('INSERT INTO promotion_codes(promotion_id,user_id,code,status,uses,created_by,created_at) VALUES(?,?,?,?,?,?,?)',(pid,uid,code,'active',0,user['id'],now()))
                        db.execute('INSERT INTO messages(sender_user_id,recipient_user_id,subject,body,created_at) VALUES(?,?,?,?,?)',
                                   (user['id'],uid,f'Tienes una promoción de {cname}',f'{pr["title"]}'+(f' · {pr["value_text"]}' if pr['value_text'] else '')+f'. Válida hasta el {pr["valid_until"]}. Encontrarás tu QR en Recompensas → Mis promociones.',now()))
                        notify_user(db,uid,'promotion_received',{'center':cname,'promo_title':pr['title'],'promo_value':pr['value_text'] or '','valid_until':'/'.join(reversed(pr['valid_until'].split('-')))},('promotion',pid))
                        created+=1
                    audit(db,user['id'],'promotion_assigned','promotion',pid,{'created':created,'skipped':skipped}); db.commit()
                    self.send_json({'ok':True,'created':created,'skipped':skipped}); return
                if path.startswith('/api/center/promo-codes/') and path.endswith('/revoke'):
                    user=require_user(self,db); require_role(user,{'center'}); code=path.split('/')[4].upper()
                    row=db.execute('SELECT pc.id FROM promotion_codes pc JOIN promotions p ON p.id=pc.promotion_id WHERE pc.code=? AND p.center_id=?',(code,user['center_id'])).fetchone()
                    if not row: raise PermissionError('Este código no es de una promoción de tu centro.')
                    db.execute("UPDATE promotion_codes SET status='revoked',revoked_at=? WHERE id=?",(now(),row['id'])); audit(db,user['id'],'promo_code_revoked','promotion_code',row['id']); db.commit()
                    self.send_json({'ok':True}); return
                if path.startswith('/api/center/promotions/') and path.endswith('/partner'):
                    user=require_user(self,db); require_role(user,{'center'}); pid=int(path.split('/')[4]); act=json_body(self).get('action')
                    if act not in ('accepted','declined'): raise ValueError('Respuesta no válida.')
                    if not db.execute('UPDATE promotion_partners SET status=?,updated_at=? WHERE promotion_id=? AND center_id=?',(act,now(),pid,user['center_id'])).rowcount: raise PermissionError('Tu centro no está invitado a esta promoción.')
                    audit(db,user['id'],'promotion_partner_'+act,'promotion',pid); db.commit(); self.send_json({'ok':True}); return
                if path.startswith('/api/promo/') and path.endswith('/redeem'):
                    user=require_user(self,db); require_role(user,{'center'}); code=path.split('/')[3].upper(); note=clean_text(json_body(self).get('note'),200) or ''
                    db.execute('BEGIN IMMEDIATE')
                    row=db.execute(PROMO_CODE_SQL,(code,)).fetchone()
                    if not row: db.rollback(); self.send_json({'error':'Este código promocional no existe.'},404); return
                    pay=promo_code_payload(db,row,user)
                    if pay['viewer']!='center_ok': db.rollback(); raise PermissionError('Esta promoción no es válida en tu centro.')
                    if pay['state']!='active': db.rollback(); raise ValueError(f"No se puede canjear: {pay['state_text'].lower()}.")
                    if db.execute('UPDATE promotion_codes SET uses=uses+1 WHERE id=? AND uses<?',(row['id'],row['uses_per_code'])).rowcount!=1: db.rollback(); raise ValueError('Este código acaba de usarse.')
                    db.execute('INSERT INTO promotion_redemptions(code_id,center_id,redeemed_by,note,created_at) VALUES(?,?,?,?,?)',(row['id'],user['center_id'],user['id'],note,now()))
                    audit(db,user['id'],'promo_redeemed','promotion_code',row['id']); db.commit()
                    self.send_json({'ok':True,'promo':promo_code_payload(db,db.execute(PROMO_CODE_SQL,(code,)).fetchone(),user)}); return
                if path=='/api/admin/payments/resolve':
                    # A payment under review (amount or currency did not match): the administrator accepts it or flags it for refund.
                    user=require_user(self,db); require_role(user,{'admin'}); data=json_body(self); oid=int(data.get('id') or 0); act=data.get('action')
                    order=db.execute('SELECT * FROM payment_orders WHERE id=?',(oid,)).fetchone()
                    if not order or order['status']!='review': raise ValueError('Ese pago no está en revisión.')
                    if act=='accept':
                        db.execute("UPDATE payment_orders SET status='paid',paid_at=COALESCE(paid_at,?),updated_at=? WHERE id=?",(now(),now(),oid))
                        if order['booking_id']:
                            b=db.execute('SELECT * FROM bookings WHERE id=?',(order['booking_id'],)).fetchone()
                            if b and b['slot_id'] and not b['slot_reserved']:
                                if reserve_slot_spots(db,b['slot_id'],max(1,int(b['participants'] or 1))): db.execute('UPDATE bookings SET slot_reserved=1 WHERE id=?',(b['id'],))
                            was_confirmed=bool(b and b['status']=='confirmed')
                            db.execute("UPDATE bookings SET payment_status='paid',payment_method='card',status=CASE WHEN status IN ('pending','confirmed') THEN 'confirmed' ELSE status END,updated_at=? WHERE id=?",(now(),order['booking_id']))
                            notify_booking(db,order['booking_id'],'paid',{'was_confirmed':was_confirmed})
                        audit(db,user['id'],'payment_review_accepted','payment_order',oid)
                    elif act=='refund':
                        # The money is in the provider's Stripe account (direct charge): the provider makes the refund.
                        got=float(order['amount_received'] or order['amount'] or 0)
                        db.execute("UPDATE payment_orders SET status='paid',paid_at=COALESCE(paid_at,?),incident='refund_pending',incident_note='Importe distinto al de la reserva: devolución pedida al prestador',incident_at=?,incident_by=?,updated_at=? WHERE id=?",(now(),now(),user['id'],now(),oid))
                        if order['booking_id']:
                            db.execute("UPDATE bookings SET payment_status='review',refund_proposed=?,refund_status='proposed',refund_proposed_at=?,updated_at=? WHERE id=?",(got,now(),now(),order['booking_id']))
                            notify_booking(db,order['booking_id'],'refund_reminder')
                            db.execute("INSERT INTO messages(sender_user_id,recipient_user_id,booking_id,subject,body,created_at,kind) VALUES(?,?,?,?,?,?,'system')",(user['id'],order['user_id'],order['booking_id'],'Vamos a devolverte tu pago','Hemos detectado una diferencia en el importe de tu pago y hemos pedido al centro que te lo devuelva. Te avisaremos por email cuando esté hecho.',now()))
                        audit(db,user['id'],'payment_review_refund','payment_order',oid)
                    else: raise ValueError('Acción no válida.')
                    db.commit(); self.send_json({'ok':True}); return
                if path=='/api/admin/site-themes':
                    user=require_user(self,db); require_role(user,{'admin'}); data=json_body(self); tid=int(data.get('id') or 0)
                    name=clean_text(data.get('name'),80)
                    if not name: raise ValueError('Ponle un nombre al tema (por ejemplo «Verano» o «Navidad»).')
                    accent=data.get('accent') if data.get('accent') in THEME_ACCENTS else 'oceano'
                    mode=data.get('mode') if data.get('mode') in THEME_MODES else 'schedule'
                    scope=data.get('scope') if data.get('scope') in THEME_SCOPES else 'all'
                    a,b=_md(data.get('starts_on')),_md(data.get('ends_on'))
                    if mode=='schedule' and not (a and b): raise ValueError('Indica desde qué día y hasta qué día se muestra (cada año).')
                    ribbon=clean_text(data.get('ribbon'),90) or ''
                    if mode=='always': db.execute("UPDATE site_themes SET mode='schedule' WHERE mode='always' AND id<>? AND scope=?",(tid,scope))
                    if tid:
                        if not db.execute('SELECT 1 FROM site_themes WHERE id=?',(tid,)).fetchone(): self.send_json({'error':'Tema no encontrado'},404); return
                        db.execute('UPDATE site_themes SET name=?,accent=?,ribbon=?,mode=?,scope=?,starts_on=?,ends_on=?,updated_at=?,updated_by=? WHERE id=?',(name,accent,ribbon,mode,scope,a,b,now(),user['id'],tid))
                    else:
                        tid=db.execute('INSERT INTO site_themes(name,accent,ribbon,mode,scope,starts_on,ends_on,created_at,updated_at,updated_by) VALUES(?,?,?,?,?,?,?,?,?,?)',(name,accent,ribbon,mode,scope,a,b,now(),now(),user['id'])).lastrowid
                    audit(db,user['id'],'site_theme_saved','site_theme',tid); db.commit(); SITE_MEDIA.invalidate(); self.send_json({'ok':True,'id':tid}); return
                if path=='/api/admin/site-themes/delete':
                    user=require_user(self,db); require_role(user,{'admin'}); tid=int(json_body(self).get('id') or 0)
                    imgs=[r['image_url'] for r in db.execute('SELECT image_url FROM site_theme_media WHERE theme_id=?',(tid,)).fetchall()]
                    db.execute('DELETE FROM site_theme_media WHERE theme_id=?',(tid,)); db.execute('DELETE FROM site_themes WHERE id=?',(tid,))
                    audit(db,user['id'],'site_theme_deleted','site_theme',tid); db.commit()
                    for u in imgs: delete_public_image(u)
                    SITE_MEDIA.invalidate(); self.send_json({'ok':True}); return
                if path=='/api/admin/site-theme-media':
                    user=require_user(self,db); require_role(user,{'admin'}); fields,files=parse_multipart(self)
                    tid=int(fields.get('theme_id') or 0); key=clean_text(fields.get('key'),80) or ''
                    if not db.execute('SELECT 1 FROM site_themes WHERE id=?',(tid,)).fetchone(): self.send_json({'error':'Tema no encontrado'},404); return
                    if not site_media_key_ok(key): raise ValueError('Esa imagen no existe en la web.')
                    row=db.execute('SELECT image_url,credit FROM site_theme_media WHERE theme_id=? AND key=?',(tid,key)).fetchone()
                    old=row['image_url'] if row else None
                    if fields.get('reset')=='1' or not (files.get('file') or old):
                        db.execute('DELETE FROM site_theme_media WHERE theme_id=? AND key=?',(tid,key)); db.commit(); delete_public_image(old)
                        SITE_MEDIA.invalidate(); self.send_json({'ok':True}); return
                    url=save_public_image(files.get('file'),f'theme_{tid}_'+re.sub(r'[^a-z0-9]+','_',key)) if files.get('file') else old
                    credit=clean_text(fields.get('credit'),200) if 'credit' in fields else (row['credit'] if row else '')
                    db.execute('INSERT INTO site_theme_media(theme_id,key,image_url,credit,updated_at) VALUES(?,?,?,?,?) ON CONFLICT(theme_id,key) DO UPDATE SET image_url=excluded.image_url,credit=excluded.credit,updated_at=excluded.updated_at',(tid,key,url,credit,now()))
                    audit(db,user['id'],'site_theme_media','site_theme',tid,key); db.commit()
                    if old and old!=url: delete_public_image(old)
                    SITE_MEDIA.invalidate(); self.send_json({'ok':True,'url':url}); return
                if path=='/api/admin/site-media':
                    user=require_user(self,db); require_role(user,{'admin'}); fields,files=parse_multipart(self)
                    key=clean_text(fields.get('key'),80) or ''
                    if not site_media_key_ok(key): raise ValueError('Esa imagen no existe en la web.')
                    row=db.execute('SELECT image_url,credit FROM site_media WHERE key=?',(key,)).fetchone()
                    old=row['image_url'] if row else None
                    if fields.get('reset')=='1':
                        db.execute('DELETE FROM site_media WHERE key=?',(key,)); audit(db,user['id'],'site_media_reset','site_media',None,key); db.commit()
                        delete_public_image(old); SITE_MEDIA.invalidate(); self.send_json({'ok':True}); return
                    url=save_public_image(files.get('file'),'site_'+re.sub(r'[^a-z0-9]+','_',key)) if files.get('file') else old
                    credit=clean_text(fields.get('credit'),200) if 'credit' in fields else (row['credit'] if row else '')
                    if not url and not credit:
                        if row: db.execute('DELETE FROM site_media WHERE key=?',(key,)); db.commit(); SITE_MEDIA.invalidate(); self.send_json({'ok':True}); return
                        raise ValueError('Adjunta una foto.')
                    db.execute('INSERT INTO site_media(key,image_url,credit,updated_at,updated_by) VALUES(?,?,?,?,?) ON CONFLICT(key) DO UPDATE SET image_url=excluded.image_url,credit=excluded.credit,updated_at=excluded.updated_at,updated_by=excluded.updated_by',(key,url,credit,now(),user['id']))
                    audit(db,user['id'],'site_media_updated','site_media',None,key); db.commit()
                    if old and old!=url: delete_public_image(old)
                    SITE_MEDIA.invalidate(); self.send_json({'ok':True,'url':url}); return
                if path=='/api/admin/travel-offer-image':
                    user=require_user(self,db); require_role(user,{'admin'}); fields,files=parse_multipart(self); tid=int(fields.get('id') or 0)
                    row=db.execute('SELECT image_path FROM travel_offers WHERE id=?',(tid,)).fetchone()
                    if not row: self.send_json({'error':'Destino no encontrado'},404); return
                    url=None if fields.get('remove')=='1' else save_public_image(files.get('file'),f'destination_{tid}')
                    db.execute('UPDATE travel_offers SET image_path=? WHERE id=?',(url,tid)); audit(db,user['id'],'travel_destination_image','travel_offer',tid); db.commit()
                    if row['image_path']!=url: delete_public_image(row['image_path'])
                    self.send_json({'ok':True,'url':url}); return
                if path=='/api/provider/experience-image':
                    user=require_user(self,db); fields,files=parse_multipart(self); eid=int(fields.get('id') or 0)
                    exp=db.execute('SELECT * FROM travel_experiences WHERE id=?',(eid,)).fetchone()
                    if not exp: self.send_json({'error':'Experiencia no encontrada'},404); return
                    if not (user['role']=='admin' or exp['provider_user_id']==user['id'] or (exp['center_id'] and exp['center_id']==user['center_id'])): raise PermissionError('Esta experiencia no es tuya.')
                    url=None if fields.get('remove')=='1' else save_public_image(files.get('file'),f'experience_{eid}')
                    db.execute('UPDATE travel_experiences SET image_url=?,updated_at=? WHERE id=?',(url,now(),eid)); audit(db,user['id'],'travel_experience_image','travel_experience',eid); db.commit()
                    if exp['image_url']!=url: delete_public_image(exp['image_url'])
                    TRAVEL.invalidate(); self.send_json({'ok':True,'url':url}); return
                if path.startswith('/api/dive-points/') and '/suggest' in path:
                    user=require_user(self,db); pid=int(path.split('/')[3]); data=json_body(self)
                    if not db.execute('SELECT 1 FROM dive_points WHERE id=? AND active=1',(pid,)).fetchone(): self.send_json({'error':'Punto no encontrado'},404); return
                    cur=db.execute('INSERT INTO point_position_suggestions(dive_point_id,user_id,latitude,longitude,note,status,created_at) VALUES(?,?,?,?,?,?,?)',(pid,user['id'],float(data.get('latitude')),float(data.get('longitude')),clean_text(data.get('note'),2000),'pending',now())); audit(db,user['id'],'position_suggested','point_position_suggestion',cur.lastrowid); db.commit(); self.send_json({'ok':True}); return
                if path=='/api/dive-points/update':
                    user=require_user(self,db); require_role(user,{'admin','center'}); data=json_body(self); pid=int(data['id']); row=db.execute('SELECT * FROM dive_points WHERE id=?',(pid,)).fetchone()
                    if not row: self.send_json({'error':'Punto no encontrado'},404); return
                    if user['role']=='center' and row['center_id']!=user['center_id']: raise PermissionError('No puedes modificar este punto.')
                    if user['role']=='center' and ('latitude' in data or 'longitude' in data): raise PermissionError('La posición oficial no puede modificarse directamente. Envía una corrección para que el administrador la revise.')
                    db.execute('''UPDATE dive_points SET name=?,country=?,region=?,dive_type=?,latitude=?,longitude=?,difficulty=?,min_depth=?,max_depth=?,description=?,access_info=?,center_id=?,recommended_certification_id=?,verification_status=?,updated_by_user_id=?,updated_at=? WHERE id=?''',(clean_text(data.get('name'),180),clean_text(data.get('country'),100),clean_text(data.get('region'),120),clean_text(data.get('dive_type'),100),float(data.get('latitude')),float(data.get('longitude')),clean_text(data.get('difficulty'),50),data.get('min_depth') or None,data.get('max_depth') or None,clean_text(data.get('description'),5000),clean_text(data.get('access_info'),3000),data.get('center_id') if user['role']=='admin' else user['center_id'],int(data['recommended_certification_id']) if data.get('recommended_certification_id') else None,'verified' if user['role']=='admin' else 'pending_review',user['id'],now(),pid)); audit(db,user['id'],'dive_point_updated','dive_point',pid); db.commit(); self.send_json({'ok':True}); return
                if path=='/api/travel-experiences':
                    user=require_user(self,db)
                    data=json_body(self)
                    if user['role'] not in {'admin','center','freelance'}: raise PermissionError('Solo un centro o un perfil freelance puede publicar experiencias.')
                    tid=resolve_travel_offer(db,data)
                    if not tid: raise ValueError('Elige un destino o escribe uno nuevo.')
                    if not clean_text(data.get('title'),180): raise ValueError('Ponle un título a la experiencia.')
                    provider_type=user['role'] if user['role'] in {'center','freelance'} else clean_text(data.get('provider_type'),20)
                    center_id=user['center_id'] if user['role']=='center' else (int(data.get('center_id') or 0) or None)
                    # Verified centers publish directly (the admin can still hide it); freelance proposals are reviewed.
                    status='published' if user['role'] in {'admin','center'} else 'pending'
                    cur=db.execute('''INSERT INTO travel_experiences(travel_offer_id,title,provider_user_id,center_id,provider_type,summary,description,start_date,end_date,price,currency,spots_total,spots_available,includes,conditions,status,active,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(tid,clean_text(data.get('title'),180),user['id'],center_id,provider_type,clean_text(data.get('summary'),500),clean_text(data.get('description'),5000),clean_text(data.get('start_date'),30),clean_text(data.get('end_date'),30),float(data.get('price')) if data.get('price') not in (None,'') else None,clean_text(data.get('currency'),8) or 'EUR',int(data.get('spots_total')) if data.get('spots_total') not in (None,'') else None,int(data.get('spots_available')) if data.get('spots_available') not in (None,'') else None,clean_text(data.get('includes'),3000),clean_text(data.get('conditions'),3000),status,1,now(),now())); audit(db,user['id'],'travel_experience_created','travel_experience',cur.lastrowid); db.commit(); self.send_json({'ok':True,'id':cur.lastrowid,'status':status}); return
                if path=='/api/admin/travel-offers':
                    user=require_user(self,db); require_role(user,{'admin'}); data=json_body(self)
                    tid=int(data.get('id') or 0)
                    current=db.execute('SELECT image_path FROM travel_offers WHERE id=?',(tid,)).fetchone() if tid else None
                    image=clean_text(data.get('image_path'),300) if 'image_path' in data else (current['image_path'] if current else None)
                    vals=(clean_text(data.get('title'),180),clean_text(data.get('region'),100),clean_text(data.get('kind'),60),image,clean_text(data.get('summary'),500),clean_text(data.get('description'),5000))
                    if tid:
                        if not db.execute('SELECT 1 FROM travel_offers WHERE id=?',(tid,)).fetchone(): self.send_json({'error':'Destino no encontrado'},404); return
                        db.execute('UPDATE travel_offers SET title=?,region=?,kind=?,image_path=?,summary=?,description=? WHERE id=?',vals+(tid,)); audit(db,user['id'],'travel_destination_updated','travel_offer',tid)
                    else:
                        cur=db.execute('INSERT INTO travel_offers(title,region,kind,image_path,summary,description,active) VALUES(?,?,?,?,?,?,1)',vals); tid=cur.lastrowid; audit(db,user['id'],'travel_destination_created','travel_offer',tid)
                    db.commit(); self.send_json({'ok':True,'id':tid}); return
                if path=='/api/experience-bookings':
                    user=require_user(self,db); data=json_body(self); eid=int(data.get('travel_experience_id') or 0); participants=max(1,int(data.get('participants') or 1))
                    exp=db.execute('SELECT * FROM travel_experiences WHERE id=? AND active=1 AND status=\'published\'',(eid,)).fetchone()
                    if not exp: self.send_json({'error':'Experiencia no disponible.'},404); return
                    if exp['spots_available'] is not None and participants>exp['spots_available']: raise ValueError('No hay suficientes plazas disponibles.')
                    cur=db.execute('INSERT INTO experience_bookings(travel_experience_id,user_id,participants,notes,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?)',(eid,user['id'],participants,clean_text(data.get('notes'),2000),'requested',now(),now()))
                    ebid=cur.lastrowid
                    if exp['spots_available'] is not None: db.execute('UPDATE travel_experiences SET spots_available=spots_available-?,updated_at=? WHERE id=?',(participants,now(),eid))
                    price=float(exp['price'] or 0)
                    notify_user(db,user['id'],'experience_request',{'experience':exp['title'],'participants':participants},('experience_booking',ebid))
                    _pctx={'experience':exp['title'],'participants':participants,'diver_name':user['fullname'],'notes':clean_text(data.get('notes'),2000) or '','panel_exp_url':public_site_url()+'/#/admin?tab=experiences'}
                    _rcp=center_recipients(db,exp['center_id']) if exp['center_id'] else []
                    if not _rcp and exp['provider_user_id']:
                        _pu=db.execute('SELECT id,fullname,email FROM users WHERE id=?',(exp['provider_user_id'],)).fetchone()
                        if _pu: _rcp=[(_pu['email'],_pu['fullname'],user_lang(db,_pu['id']))]
                    for _em,_nm,_lg in _rcp: queue_email(db,'center_experience_request',_em,_nm,_pctx,_lg,('experience_booking',ebid))
                    audit(db,user['id'],'experience_booking_requested','experience_booking',ebid,{'experience_id':eid,'participants':participants}); db.commit(); self.send_json({'ok':True,'id':ebid,'payment_required':price>0,'price':price,'currency':exp['currency'] or 'EUR'}); return
                if path=='/api/admin/travel-experiences/status':
                    user=require_user(self,db); require_role(user,{'admin'}); data=json_body(self); eid=int(data.get('id')); status=clean_text(data.get('status'),30)
                    if status not in {'published','rejected','pending'}: raise ValueError('Estado no válido.')
                    db.execute('UPDATE travel_experiences SET status=?,updated_at=? WHERE id=?',(status,now(),eid)); audit(db,user['id'],'travel_experience_status','travel_experience',eid,{'status':status}); db.commit(); self.send_json({'ok':True}); return
                if path=='/api/centers':
                    user=require_user(self,db); require_role(user,{'admin'}); data=json_body(self)
                    cur=db.execute('''INSERT INTO centers(name,country,region,city,address,website,phone,email,description,specialties,latitude,longitude,active,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(clean_text(data.get('name'),180),clean_text(data.get('country'),100),clean_text(data.get('region'),120),clean_text(data.get('city'),100),clean_text(data.get('address'),250),clean_url_field(data.get('website'),250),clean_text(data.get('phone'),60),clean_text(data.get('email'),160),clean_text(data.get('description'),5000),clean_text(data.get('specialties'),2000),float(data.get('latitude') or 0),float(data.get('longitude') or 0),1,now(),now())); audit(db,user['id'],'center_created','center',cur.lastrowid); db.commit(); self.send_json({'ok':True,'id':cur.lastrowid}); return
                if path=='/api/centers/update':
                    user=require_user(self,db); require_role(user,{'admin'}); data=json_body(self); cid=int(data.get('id') or 0)
                    if not db.execute('SELECT 1 FROM centers WHERE id=?',(cid,)).fetchone(): raise ValueError('Centro no encontrado.')
                    db.execute('''UPDATE centers SET name=?,country=?,region=?,city=?,address=?,website=?,phone=?,email=?,description=?,specialties=?,latitude=?,longitude=?,logo_url=?,updated_at=? WHERE id=?''',(clean_text(data.get('name'),180),clean_text(data.get('country'),100),clean_text(data.get('region'),120),clean_text(data.get('city'),100),clean_text(data.get('address'),250),clean_url_field(data.get('website'),250),clean_text(data.get('phone'),60),clean_text(data.get('email'),160),clean_text(data.get('description'),5000),clean_text(data.get('specialties'),2000),float(data.get('latitude') or 0),float(data.get('longitude') or 0),wsec.clean_local_or_http_url(data.get('logo_url'),500) or None,now(),cid))
                    audit(db,user['id'],'center_updated','center',cid); db.commit(); self.send_json({'ok':True,'id':cid}); return
                if path=='/api/admin/users/role':
                    user=require_user(self,db); require_role(user,{'admin'}); data=json_body(self)
                    uid=int(data['user_id']); role=clean_text(data.get('role'),30); center_id=int(data.get('center_id') or 0) or None
                    if role not in ROLES: raise ValueError('Rol no válido.')
                    if role=='center' and not center_id: raise ValueError('Una cuenta de centro necesita un centro asociado.')
                    if center_id and not db.execute('SELECT 1 FROM centers WHERE id=? AND active=1',(center_id,)).fetchone(): raise ValueError('Centro no válido.')
                    if uid==user['id'] and role!='admin': raise ValueError('No puedes quitarte a ti mismo el rol de administración.')
                    db.execute('UPDATE users SET role=?,center_id=? WHERE id=?',(role,center_id,uid))
                    db.execute('DELETE FROM sessions WHERE user_id=?',(uid,))  # a role change takes effect at once: the user signs in again
                    audit(db,user['id'],'user_role_updated','user',uid,{'role':role,'center_id':center_id}); db.commit(); self.send_json({'ok':True}); return
                if path=='/api/qr/create':
                    user=require_user(self,db); require_role(user,{'admin','center'}); data=json_body(self); cid=int(data.get('center_id') or user['center_id'])
                    if user['role']=='center' and cid!=user['center_id']: raise PermissionError('No puedes crear QR para otro centro.')
                    if not db.execute('SELECT 1 FROM centers WHERE id=? AND active=1',(cid,)).fetchone(): raise ValueError('Centro no válido.')
                    purpose=clean_text(data.get('purpose'),40) or 'center'
                    allowed={'center','diver','dive','booking'}
                    if purpose not in allowed: raise ValueError('Tipo de QR no válido.')
                    ref=int(data.get('reference_id') or 0) or None
                    if purpose=='dive' and ref and not db.execute('SELECT 1 FROM service_slots s JOIN provider_services ps ON ps.id=s.service_id WHERE s.id=? AND ps.center_id=?',(ref,cid)).fetchone(): raise PermissionError('La salida no pertenece a tu centro.')
                    if purpose=='booking' and ref and not db.execute('SELECT 1 FROM bookings WHERE id=? AND center_id=?',(ref,cid)).fetchone(): raise ValueError('Reserva no válida.')
                    code=secrets.token_urlsafe(9).replace('-','').replace('_','')[:12].upper()
                    default_labels={'center':'Identificación del centro','diver':'Check-in del buceador','dive':'Inmersión','booking':'Reserva'}
                    label=clean_text(data.get('label'),120) or default_labels[purpose]
                    cur=db.execute('INSERT INTO qr_codes(center_id,code,label,purpose,reference_id,active,created_at) VALUES(?,?,?,?,?,?,?)',(cid,code,label,purpose,ref,1,now())); audit(db,user['id'],'qr_created','qr_code',cur.lastrowid,{'purpose':purpose,'reference_id':ref}); db.commit(); self.send_json({'ok':True,'code':code,'purpose':purpose,'reference_id':ref}); return
                if path.startswith('/api/checkin/'):
                    user=require_user(self,db); code=path.rsplit('/',1)[1]; qr=db.execute('SELECT * FROM qr_codes WHERE code=? AND active=1',(code,)).fetchone()
                    if not qr: self.send_json({'error':'QR no válido o caducado.'},404); return
                    data=json_body(self)
                    # G5: the check-in shares the diver's profile with the centre only after an explicit «Compartir mis datos».
                    if not data.get('share_consent'):
                        cname=db.execute('SELECT name FROM centers WHERE id=?',(qr['center_id'],)).fetchone()
                        self.send_json({'error':'consent_required','needs_consent':True,'center_id':qr['center_id'],'center_name':cname[0] if cname else ''},409); return
                    grant_data_share(db,user['id'],qr['center_id'],'qr_checkin')
                    existing=db.execute('SELECT id FROM center_links WHERE user_id=? AND center_id=?',(user['id'],qr['center_id'])).fetchone()
                    if existing: db.execute('UPDATE center_links SET last_checkin=? WHERE id=?',(now(),existing['id']))
                    else: db.execute('INSERT INTO center_links(user_id,center_id,first_checkin,last_checkin) VALUES(?,?,?,?)',(user['id'],qr['center_id'],now(),now()))
                    audit(db,user['id'],'center_checkin','center',qr['center_id'],{'code':code,'purpose':qr['purpose'],'reference_id':qr['reference_id']}); sync_user_rewards(db,user['id']); db.commit();
                    payload={'ok':True,'center_id':qr['center_id'],'center_name':db.execute('SELECT name FROM centers WHERE id=?',(qr['center_id'],)).fetchone()[0],'purpose':qr['purpose'],'reference_id':qr['reference_id'],'label':qr['label']}
                    if qr['purpose']=='dive' and qr['reference_id']:
                        row=db.execute('''SELECT s.id,s.slot_date,s.slot_time,s.spots_total,s.spots_available,ps.title AS service_title,dp.name AS point_name,dp.country FROM service_slots s JOIN provider_services ps ON ps.id=s.service_id LEFT JOIN service_slot_points sp ON sp.slot_id=s.id LEFT JOIN dive_points dp ON dp.id=sp.dive_point_id WHERE s.id=? AND ps.center_id=? LIMIT 1''',(qr['reference_id'],qr['center_id'])).fetchone()
                        if row: payload['dive']=dict(row)
                    if qr['purpose']=='booking' and qr['reference_id']:
                        row=db.execute('''SELECT b.id,b.booking_date,b.booking_time,b.participants,b.status,ps.title AS service_title,dp.name AS point_name FROM bookings b LEFT JOIN provider_services ps ON ps.id=b.service_id LEFT JOIN dive_points dp ON dp.id=b.dive_point_id WHERE b.id=? AND b.center_id=?''',(qr['reference_id'],qr['center_id'])).fetchone()
                        if row: payload['booking']=dict(row)
                    self.send_json(payload); return
                if path=='/api/admin/suggestions/review':
                    user=require_user(self,db); require_role(user,{'admin'}); data=json_body(self); sid=int(data['id']); decision=data.get('decision'); sug=db.execute('SELECT * FROM point_position_suggestions WHERE id=?',(sid,)).fetchone()
                    if not sug: self.send_json({'error':'Propuesta no encontrada'},404); return
                    if decision=='approve':
                        db.execute('UPDATE dive_points SET latitude=?,longitude=?,updated_by_user_id=?,updated_at=?,verification_status="verified" WHERE id=?',(sug['latitude'],sug['longitude'],user['id'],now(),sug['dive_point_id'])); new_status='approved'
                    else: new_status='rejected'
                    db.execute('UPDATE point_position_suggestions SET status=?,reviewed_at=?,reviewed_by_user_id=? WHERE id=?',(new_status,now(),user['id'],sid)); audit(db,user['id'],'position_suggestion_reviewed','point_position_suggestion',sid,{'decision':decision}); db.commit(); self.send_json({'ok':True}); return
                if path=='/api/admin/dive-points/review':
                    user=require_user(self,db); require_role(user,{'admin'}); data=json_body(self); pid=int(data.get('id')); decision=clean_text(data.get('decision'),20)
                    row=db.execute('SELECT * FROM dive_points WHERE id=?',(pid,)).fetchone()
                    if not row: raise ValueError('Punto no encontrado.')
                    if decision=='approve':
                        db.execute("UPDATE dive_points SET verification_status='verified',updated_by_user_id=?,updated_at=? WHERE id=?",(user['id'],now(),pid))
                    elif decision=='reject':
                        db.execute("UPDATE dive_points SET active=0,verification_status='rejected',updated_by_user_id=?,updated_at=? WHERE id=?",(user['id'],now(),pid))
                    else: raise ValueError('Decisión no válida.')
                    audit(db,user['id'],'dive_point_reviewed','dive_point',pid,{'decision':decision}); db.commit(); self.send_json({'ok':True}); return
                if path=='/api/admin/center-claims':
                    user=require_user(self,db); require_role(user,{'admin'})
                    rows=db.execute('''SELECT cc.*,u.fullname,u.email,u.username,c.name AS matched_center_name,c.website AS draft_website,
                                              sc.name AS suggested_center_name,sc.city AS suggested_center_city,sc.phone AS suggested_center_phone,sc.website AS suggested_center_website
                                         FROM center_claims cc JOIN users u ON u.id=cc.user_id LEFT JOIN centers c ON c.id=cc.center_id LEFT JOIN centers sc ON sc.id=cc.suggested_center_id
                                        WHERE cc.status='pending' ORDER BY cc.created_at DESC''').fetchall()
                    items=[]
                    for r_ in rows:
                        d=dict(r_); dom=(d.get('email') or '').rsplit('@',1)[-1].lower(); site=urlparse(d.get('website') or d.get('draft_website') or '').hostname or ''
                        d['email_matches_domain']=bool(dom and site and (site==dom or site.endswith('.'+dom) or dom.endswith('.'+site.removeprefix('www.')) or site.removeprefix('www.')==dom))
                        items.append(d)
                    self.send_json({'items':items,'methods':VERIFICATION_METHODS}); return
                if path=='/api/admin/center-claims/review':
                    # G2: approving a professional account requires saying HOW it was verified (email on the centre's own
                    # domain, a call to its public phone number or a document) and a note; it is all kept in the audit log.
                    user=require_user(self,db); require_role(user,{'admin'}); data=json_body(self); cid=int(data['id']); decision=clean_text(data.get('decision'),20); claim=db.execute('SELECT * FROM center_claims WHERE id=?',(cid,)).fetchone()
                    if not claim: raise ValueError('Solicitud no encontrada.')
                    if claim['status']!='pending': raise ValueError('Esta solicitud ya está resuelta.')
                    method=clean_text(data.get('verification_method'),30); vnote=clean_text(data.get('verification_note'),1000) or ''
                    requested=claim['requested_role'] or 'center'
                    if decision=='approve':
                        if method not in VERIFICATION_METHODS: raise ValueError('Indica cómo has verificado la cuenta: email del dominio del centro, llamada al teléfono público o documento.')
                        if len(vnote)<5: raise ValueError('Añade una nota de la verificación (por ejemplo, a qué número llamaste o qué documento revisaste).')
                        if requested=='freelance':
                            db.execute("UPDATE users SET role='freelance',requested_role='freelance' WHERE id=?",(claim['user_id'],))
                            target=None
                        else:
                            target=int(data.get('center_id') or claim['center_id'] or 0)
                            if not target: raise ValueError('Esta solicitud no tiene ficha de centro. Elige el centro que corresponde.')
                            if db.execute("SELECT 1 FROM users WHERE center_id=? AND role='center' AND id<>?",(target,claim['user_id'])).fetchone() and not data.get('allow_second_manager'):
                                raise ValueError('Ese centro ya tiene una cuenta gestora. Confirma que esta persona también debe gestionarlo.')
                            db.execute("UPDATE users SET role='center',center_id=?,requested_role='center' WHERE id=?",(target,claim['user_id']))
                            db.execute("UPDATE centers SET active=1,verification_status='verified',data_confidence='provider_verified',updated_at=? WHERE id=?",(now(),target))
                            if claim['center_id'] and claim['center_id']!=target:
                                # The administrator linked the request to another existing centre: the unused draft is discarded.
                                db.execute("UPDATE centers SET active=0,verification_status='discarded',updated_at=? WHERE id=? AND verification_status='pending_provider'",(now(),claim['center_id']))
                            db.execute("INSERT OR IGNORE INTO center_members(center_id,user_id,member_role,created_at) VALUES(?,?,'owner',?)",(target,claim['user_id'],now()))
                        db.execute("UPDATE center_claims SET status='approved',center_id=COALESCE(?,center_id),reviewed_at=?,reviewed_by_user_id=?,verification_method=?,verification_note=? WHERE id=?",(target,now(),user['id'],method,vnote,cid))
                        db.execute('DELETE FROM sessions WHERE user_id=?',(claim['user_id'],))
                        cname=db.execute('SELECT name FROM centers WHERE id=?',(target,)).fetchone()['name'] if target else db.execute('SELECT fullname FROM users WHERE id=?',(claim['user_id'],)).fetchone()['fullname']
                        notify_user(db,claim['user_id'],'center_verified',{'center':cname},('center',target) if target else ('user',claim['user_id']))
                        DIRECTORY.invalidate(); PROMOS.invalidate()
                    elif decision=='reject':
                        db.execute("UPDATE center_claims SET status='rejected',reviewed_at=?,reviewed_by_user_id=?,verification_method=?,verification_note=? WHERE id=?",(now(),user['id'],method,vnote,cid))
                        if claim['center_id']: db.execute("UPDATE centers SET active=0,verification_status='rejected',updated_at=? WHERE id=? AND verification_status='pending_provider'",(now(),claim['center_id']))
                        db.execute("UPDATE users SET requested_role='recreational' WHERE id=?",(claim['user_id'],))
                    else: raise ValueError('Decisión no válida.')
                    audit(db,user['id'],'center_claim_reviewed','center_claim',cid,{'decision':decision,'method':method,'note':vnote[:200]}); db.commit(); self.send_json({'ok':True}); return
                if path=='/api/center/profile':
                    user=require_user(self,db); require_role(user,{'center'}); data=json_body(self); target=int(user['center_id'] or 0)
                    if not target: raise ValueError('La cuenta aún no tiene un centro aprobado.')
                    db.execute('''UPDATE centers SET name=?,country=?,region=?,city=?,address=?,website=?,phone=?,email=?,description=?,specialties=?,latitude=?,longitude=?,updated_at=? WHERE id=?''',(clean_text(data.get('name'),180),clean_text(data.get('country'),100),clean_text(data.get('region'),120),clean_text(data.get('city'),100),clean_text(data.get('address'),250),clean_url_field(data.get('website'),250),clean_text(data.get('phone'),60),clean_text(data.get('email'),160),clean_text(data.get('description'),5000),clean_text(data.get('specialties'),2000),float(data.get('latitude') or 0),float(data.get('longitude') or 0),now(),target)); audit(db,user['id'],'center_profile_updated','center',target); db.commit(); self.send_json({'ok':True}); return
                if path=='/api/rewards/seed':
                    user=require_user(self,db); sync_user_rewards(db,user['id']); db.commit(); self.send_json({'ok':True}); return
                if path=='/api/rewards/redeem':
                    user=require_user(self,db); data=json_body(self); offer_id=int(data.get('offer_id') or 0)
                    offer=db.execute('SELECT * FROM reward_offers WHERE id=? AND active=1',(offer_id,)).fetchone()
                    if not offer: raise ValueError('Recompensa no disponible.')
                    if offer['stock'] is not None and offer['stock']<=0: raise ValueError('Esta recompensa ya no tiene disponibilidad.')
                    sync_user_rewards(db,user['id'])
                    balance=float(db.execute('SELECT COALESCE(SUM(amount),0) FROM wallet_transactions WHERE user_id=?',(user['id'],)).fetchone()[0] or 0)
                    cost=float(offer['cost_wallet'] or 0)
                    if balance+1e-9 < cost: raise ValueError('Todavía no tienes saldo suficiente para este canje.')
                    code='WOD-'+secrets.token_hex(4).upper()
                    db.execute('INSERT INTO reward_redemptions(offer_id,user_id,code,cost_wallet,status,created_at) VALUES(?,?,?,?,?,?)',(offer_id,user['id'],code,cost,'issued',now()))
                    db.execute('INSERT INTO wallet_transactions(user_id,amount,description,created_at) VALUES(?,?,?,?)',(user['id'],-cost,'Canje: '+offer['title'],now()))
                    if offer['stock'] is not None: db.execute('UPDATE reward_offers SET stock=stock-1,updated_at=? WHERE id=?',(now(),offer_id))
                    audit(db,user['id'],'reward_redeemed','reward_offer',offer_id,{'code':code,'cost':cost}); db.commit(); self.send_json({'ok':True,'code':code,'balance':round(balance-cost,2)}); return
                if path=='/api/rewards/offers':
                    user=require_user(self,db); rows=db.execute('''SELECT ro.*,c.name AS center_name FROM reward_offers ro LEFT JOIN centers c ON c.id=ro.center_id WHERE ro.active=1 AND (ro.stock IS NULL OR ro.stock>0) ORDER BY ro.cost_wallet,ro.id''').fetchall(); self.send_json({'items':[dict(r) for r in rows]}); return
                if path=='/api/provider/wallet-grant':
                    user=require_user(self,db); require_role(user,{'admin','center'}); data=json_body(self)
                    target_id=int(data.get('user_id') or 0); amount=float(data.get('amount') or 0)
                    if amount<=0 or amount>1000: raise ValueError('El importe debe estar entre 0 y 1000.')
                    if not db.execute('SELECT 1 FROM users WHERE id=?',(target_id,)).fetchone(): raise ValueError('Usuario no encontrado.')
                    if user['role']=='center':
                        cid=int(user['center_id'] or 0)
                        linked=db.execute('SELECT 1 FROM center_links WHERE user_id=? AND center_id=?',(target_id,cid)).fetchone()
                        booking=db.execute('SELECT 1 FROM bookings WHERE user_id=? AND center_id=? LIMIT 1',(target_id,cid)).fetchone()
                        if not linked and not booking: raise PermissionError('Solo puedes conceder saldo a clientes vinculados o con una reserva en tu centro.')
                    reason=clean_text(data.get('reason'),250) or 'Saldo promocional concedido por el centro'
                    db.execute('INSERT INTO wallet_transactions(user_id,amount,description,created_at) VALUES(?,?,?,?)',(target_id,amount,reason,now()))
                    audit(db,user['id'],'wallet_granted','user',target_id,{'amount':amount,'reason':reason,'center_id':user.get('center_id')}); db.commit()
                    self.send_json({'ok':True,'user_id':target_id,'amount':amount}); return
                if path=='/api/travel-experiences/update':
                    user=require_user(self,db); require_role(user,{'center','freelance'}); data=json_body(self); eid=int(data.get('id') or 0)
                    exp=db.execute('SELECT * FROM travel_experiences WHERE id=?',(eid,)).fetchone()
                    if not exp or not (exp['provider_user_id']==user['id'] or (exp['center_id'] and exp['center_id']==user['center_id'])): raise PermissionError('Esta experiencia no es tuya.')
                    if data.get('delete'):
                        db.execute('UPDATE travel_experiences SET active=0,updated_at=? WHERE id=?',(now(),eid)); audit(db,user['id'],'travel_experience_hidden','travel_experience',eid); db.commit(); self.send_json({'ok':True}); return
                    if exp['service_id']: raise ValueError('Esta experiencia se edita desde su servicio en «Servicios y tarifas».')
                    tid=resolve_travel_offer(db,data) or exp['travel_offer_id']
                    num=lambda v,f: f(v) if v not in (None,'') else None
                    status='published' if user['role']=='center' else exp['status']
                    db.execute('UPDATE travel_experiences SET travel_offer_id=?,title=?,summary=?,description=?,start_date=?,end_date=?,price=?,spots_total=?,spots_available=?,includes=?,conditions=?,status=?,active=1,updated_at=? WHERE id=?',
                               (tid,clean_text(data.get('title'),180) or exp['title'],clean_text(data.get('summary'),500),clean_text(data.get('description'),5000),clean_text(data.get('start_date'),30),clean_text(data.get('end_date'),30),num(data.get('price'),float),num(data.get('spots_total'),int),num(data.get('spots_available'),int),clean_text(data.get('includes'),3000),clean_text(data.get('conditions'),3000),status,now(),eid))
                    audit(db,user['id'],'travel_experience_updated','travel_experience',eid); db.commit(); self.send_json({'ok':True}); return
                if path=='/api/provider/experience-bookings/status':
                    user=require_user(self,db); require_role(user,{'center','freelance'}); data=json_body(self); rid=int(data.get('id') or 0); status=clean_text(data.get('status'),20)
                    if status not in {'confirmed','rejected','cancelled'}: raise ValueError('Estado no válido.')
                    r=db.execute('SELECT eb.*,e.provider_user_id,e.center_id,e.spots_available,e.spots_total,e.title FROM experience_bookings eb JOIN travel_experiences e ON e.id=eb.travel_experience_id WHERE eb.id=?',(rid,)).fetchone()
                    if not r or not (r['provider_user_id']==user['id'] or (r['center_id'] and r['center_id']==user['center_id'])): raise PermissionError('Esta solicitud no es tuya.')
                    if status==r['status']: self.send_json({'ok':True,'unchanged':True}); return
                    if status in {'rejected','cancelled'} and r['status'] in {'requested','confirmed'} and r['spots_available'] is not None:
                        db.execute('UPDATE travel_experiences SET spots_available=MIN(COALESCE(spots_total,spots_available+?),spots_available+?),updated_at=? WHERE id=?',(r['participants'],r['participants'],now(),r['travel_experience_id']))
                    db.execute('UPDATE experience_bookings SET status=?,updated_by=?,updated_at=? WHERE id=?',(status,user['id'],now(),rid))
                    label={'confirmed':'confirmada','rejected':'rechazada','cancelled':'cancelada'}[status]
                    db.execute('INSERT INTO messages(sender_user_id,recipient_user_id,experience_booking_id,subject,body,created_at) VALUES(?,?,?,?,?,?)',(user['id'],r['user_id'],rid,f'Solicitud {label}',f'Tu solicitud para «{r["title"]}» ha sido {label}.',now()))
                    _lg=user_lang(db,r['user_id'])
                    _st={'confirmed':('Solicitud confirmada','tu plaza en «{experience}» está confirmada. El organizador te contactará con los detalles.'),
                         'rejected':('Solicitud no disponible','el organizador de «{experience}» no puede atender tu solicitud esta vez. Echa un vistazo a otros viajes en WORLDIVES.'),
                         'cancelled':('Solicitud cancelada','tu solicitud para «{experience}» se ha cancelado. Si habías pagado, te devolveremos el importe.')}[status]
                    notify_user(db,r['user_id'],'experience_status',{'experience':r['title'],'status_title':mail_t(_lg,_st[0]),'status_text':mail_t(_lg,_st[1],experience=r['title'])},('experience_booking',rid))
                    audit(db,user['id'],'experience_booking_status','experience_booking',rid,{'status':status}); db.commit(); self.send_json({'ok':True}); return
                if path=='/api/provider/center-cover' or path=='/api/provider/center-gallery':
                    user=require_user(self,db); require_role(user,{'center'}); cid=int(user['center_id'] or 0)
                    if not cid: raise ValueError('Tu cuenta no tiene un centro asociado.')
                    fields,files=parse_multipart(self)
                    row=db.execute('SELECT cover_url,gallery_json FROM centers WHERE id=?',(cid,)).fetchone()
                    if path.endswith('cover'):
                        url=save_public_image(files.get('file'),f'center_{cid}_cover')
                        old=row['cover_url']; db.execute('UPDATE centers SET cover_url=?,updated_at=? WHERE id=?',(url,now(),cid))
                        audit(db,user['id'],'center_cover_updated','center',cid); db.commit(); delete_public_image(old); self.send_json({'ok':True,'url':url}); return
                    gallery=center_gallery(row)
                    if len(gallery)>=MAX_GALLERY_IMAGES: raise ValueError(f'La galería admite {MAX_GALLERY_IMAGES} fotos. Elimina alguna para añadir otra.')
                    url=save_public_image(files.get('file'),f'center_{cid}_gallery'); gallery.append(url)
                    db.execute('UPDATE centers SET gallery_json=?,updated_at=? WHERE id=?',(json.dumps(gallery),now(),cid))
                    audit(db,user['id'],'center_gallery_added','center',cid); db.commit(); self.send_json({'ok':True,'url':url,'gallery':gallery}); return
                if path=='/api/provider/center-showcase':
                    # Texts and photo management for the public page; the contact data stay in center-update.
                    user=require_user(self,db); require_role(user,{'center'}); data=json_body(self); cid=int(user['center_id'] or 0)
                    if not cid: raise ValueError('Tu cuenta no tiene un centro asociado.')
                    row=db.execute('SELECT cover_url,gallery_json FROM centers WHERE id=?',(cid,)).fetchone()
                    gallery=center_gallery(row); removed=[]
                    if 'gallery' in data:
                        wanted=[x for x in (data.get('gallery') or []) if x in gallery]
                        removed=[x for x in gallery if x not in wanted]; gallery=wanted
                    cover=row['cover_url']
                    if data.get('remove_cover'): removed.append(cover); cover=None
                    db.execute('UPDATE centers SET tagline=?,languages=?,opening_hours=?,gallery_json=?,cover_url=?,updated_at=? WHERE id=?',(clean_text(data.get('tagline'),160),clean_text(data.get('languages'),160),clean_text(data.get('opening_hours'),300),json.dumps(gallery),cover,now(),cid))
                    audit(db,user['id'],'center_showcase_updated','center',cid); db.commit()
                    for u in removed: delete_public_image(u)
                    self.send_json({'ok':True}); return
                if path=='/api/center/bookings/manual':
                    # A booking entered by the center itself: phone, walk-in, email, agency...
                    user=require_user(self,db); require_role(user,{'center'}); data=json_body(self); cid=int(user['center_id'] or 0)
                    if not cid: raise ValueError('Tu cuenta no tiene un centro asociado.')
                    fullname=clean_text(data.get('fullname'),180)
                    if not fullname: raise ValueError('Indica el nombre del cliente.')
                    service_id=int(data.get('service_id') or 0)
                    service=db.execute('SELECT * FROM provider_services WHERE id=? AND center_id=?',(service_id,cid)).fetchone()
                    if not service: raise ValueError('Elige una actividad de tu centro.')
                    participants=max(1,min(200,int(data.get('participants') or 1)))
                    slot=None; slot_id=int(data.get('slot_id') or 0) or None
                    if slot_id:
                        slot=db.execute("SELECT * FROM service_slots WHERE id=? AND service_id=? AND status IN ('open','full')",(slot_id,service_id)).fetchone()
                        if not slot: raise ValueError('Esa salida ya no está disponible.')
                    bdate=slot['slot_date'] if slot else clean_text(data.get('booking_date'),10)
                    btime=slot['slot_time'] if slot else clean_text(data.get('booking_time'),5)
                    if not bdate: raise ValueError('Elige una salida o indica la fecha.')
                    status=clean_text(data.get('status'),20) or 'confirmed'
                    if status=='pending': status='requested'
                    if status not in {'confirmed','requested'}: status='confirmed'
                    if slot and status=='confirmed' and participants>int(slot['spots_available']):
                        raise ValueError(f'En esa salida solo quedan {slot["spots_available"]} plazas.')
                    total,currency,lines=booking_quote(db,cid,service,participants,bdate,as_list(data.get('extra_ids')),as_list(data.get('equipment_codes')))
                    override=data.get('price_override')
                    if override not in (None,''):
                        override=round(max(0.0,float(override)),2)
                        if abs(override-total)>=0.005: lines.append({'kind':'adjustment','label':'Ajuste del centro','unit':round(override-total,2),'qty':1,'total':round(override-total,2)})
                        total=override
                    payment_status=clean_text(data.get('payment_status'),20) or ('required' if total>0 else 'not_required')
                    if payment_status not in {'paid','required','not_required'}: payment_status='required'
                    if total<=0: payment_status='not_required'
                    point_id=None
                    if slot:
                        pr=db.execute('SELECT dive_point_id FROM service_slot_points WHERE slot_id=? LIMIT 1',(slot['id'],)).fetchone(); point_id=pr['dive_point_id'] if pr else None
                    uid=find_or_create_customer(db,fullname,data.get('email'),data.get('phone'),cid)
                    reserved=0
                    if slot and status=='confirmed':
                        if not reserve_slot_spots(db,slot['id'],participants): raise ValueError('Las plazas acaban de cambiar. Revisa la salida.')
                        reserved=1
                    codes=as_list(data.get('equipment_codes'))
                    cur=db.execute('''INSERT INTO bookings(user_id,center_id,dive_point_id,service_id,slot_id,slot_reserved,booking_date,booking_time,participants,needs_equipment,equipment_items,notes,status,price,currency,payment_status,price_breakdown,source,contact_phone,contact_email,contact_name,created_by_user_id,payment_method,internal_notes,public_token,created_at,updated_at)
                                      VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(uid,cid,point_id,service_id,slot['id'] if slot else None,reserved,bdate,btime,participants,1 if codes else 0,', '.join(l['label'] for l in lines if l['kind']=='equipment'),clean_text(data.get('notes'),2000),status,total,currency,payment_status,json.dumps(lines,ensure_ascii=False),'manual',clean_text(data.get('phone'),60),(clean_text(data.get('email'),160) or '').lower() or None,fullname,user['id'],clean_text(data.get('payment_method'),40),clean_text(data.get('internal_notes'),2000),wsec.random_token(),now(),now()))
                    if data.get('notify_client',True) and status=='confirmed': notify_booking(db,cur.lastrowid,'manual')
                    audit(db,user['id'],'booking_created_manual','booking',cur.lastrowid,{'participants':participants,'total':total}); db.commit()
                    self.send_json({'ok':True,'id':cur.lastrowid,'total':total,'status':status,'payment_status':payment_status}); return
                if path.startswith('/api/bookings/') and path.endswith('/payment'):
                    # The center records a payment taken at the desk (cash, card terminal, transfer).
                    user=require_user(self,db); require_role(user,{'center','freelance','admin'}); bid=int(path.split('/')[-2]); data=json_body(self)
                    row=db.execute('SELECT * FROM bookings WHERE id=?',(bid,)).fetchone()
                    if not row: self.send_json({'error':'Reserva no encontrada'},404); return
                    require_booking_provider(user,row)
                    pay=clean_text(data.get('payment_status'),20)
                    if pay not in {'paid','required','at_center'}: raise ValueError('Estado de pago no válido.')
                    cur_state=wbk.normalize_state(row['status'])
                    if cur_state in ('payment_in_progress','expired') and (row['booking_mode']=='payment'):
                        raise ValueError('Una reserva «Pago al reservar» solo se confirma con el pago online confirmado por Stripe.')
                    if pay!='paid' and booking_paid_online(db,bid)[2]: raise ValueError('Esta reserva tiene un pago online. Si hay que devolver dinero, usa «Devolver».')
                    if pay=='required' and not payee_ready(booking_payee(db,row)[1]): pay='at_center'
                    # Desk payment: the rest after a deposit, or the whole price. Online amounts stay as they are.
                    paid_amt=float(row['price'] or 0) if pay=='paid' else float(row['amount_paid'] or 0)
                    db.execute('UPDATE bookings SET payment_status=?,payment_method=?,amount_paid=?,amount_due=?,updated_at=? WHERE id=?',
                               (pay,clean_text(data.get('payment_method'),40) or row['payment_method'],paid_amt,round(max(0.0,float(row['price'] or 0)-paid_amt),2),now(),bid))
                    if pay=='paid' and cur_state in ('requested','accepted_pending_payment'):
                        # Paid at the desk: the place is the diver's (any open online payment is closed).
                        reserve_or_fail(db,row)
                        for o in db.execute("SELECT * FROM payment_orders WHERE booking_id=? AND status='pending'",(bid,)).fetchall():
                            expire_checkout(o); db.execute("UPDATE payment_orders SET status='cancelled',updated_at=? WHERE id=?",(now(),o['id']))
                        db.execute("UPDATE bookings SET status='confirmed',confirmed_at=?,accepted_at=COALESCE(accepted_at,?),updated_at=? WHERE id=?",(now(),now(),now(),bid))
                        notify_booking(db,bid,'confirmed')
                    audit(db,user['id'],'booking_payment_recorded','booking',bid,{'payment_status':pay}); db.commit(); self.send_json({'ok':True}); return
                if path=='/api/service-templates/save':
                    user=require_user(self,db); require_role(user,{'center','freelance'}); data=json_body(self); tid=int(data.get('id') or 0)
                    t=clean_service_template(data); cols=list(t)
                    if tid:
                        if not db.execute('SELECT 1 FROM service_templates WHERE id=? AND provider_user_id=?',(tid,user['id'])).fetchone(): raise PermissionError('Plantilla no válida.')
                        db.execute(f"UPDATE service_templates SET {','.join(c+'=?' for c in cols)},updated_at=? WHERE id=?",[t[c] for c in cols]+[now(),tid])
                    else:
                        same=db.execute('SELECT id FROM service_templates WHERE provider_user_id=? AND lower(name)=lower(?)',(user['id'],t['name'])).fetchone()
                        if same:
                            tid=same['id']; db.execute(f"UPDATE service_templates SET {','.join(c+'=?' for c in cols)},updated_at=? WHERE id=?",[t[c] for c in cols]+[now(),tid])
                        else:
                            if db.execute('SELECT COUNT(*) FROM service_templates WHERE provider_user_id=?',(user['id'],)).fetchone()[0]>=MAX_TEMPLATES_PER_PROVIDER:
                                raise ValueError(f'Has llegado al máximo de {MAX_TEMPLATES_PER_PROVIDER} plantillas. Elimina alguna para crear otra.')
                            tid=db.execute(f"INSERT INTO service_templates(provider_user_id,{','.join(cols)},created_at,updated_at) VALUES(?,{','.join('?' for _ in cols)},?,?)",[user['id']]+[t[c] for c in cols]+[now(),now()]).lastrowid
                    audit(db,user['id'],'service_template_saved','service_template',tid); db.commit(); self.send_json({'ok':True,'id':tid}); return
                if path=='/api/service-templates/delete':
                    user=require_user(self,db); require_role(user,{'center','freelance'}); data=json_body(self); tid=int(data.get('id') or 0)
                    cur=db.execute('DELETE FROM service_templates WHERE id=? AND provider_user_id=?',(tid,user['id']))
                    if not cur.rowcount: raise PermissionError('Plantilla no válida.')
                    audit(db,user['id'],'service_template_deleted','service_template',tid); db.commit(); self.send_json({'ok':True}); return
                if path=='/api/center/extras/save':
                    user=require_user(self,db); require_role(user,{'center','admin'}); data=json_body(self); cid=user['center_id'] if user['role']=='center' else int(data.get('center_id') or 0); eid=int(data.get('id') or 0)
                    if eid:
                        row=db.execute('SELECT id FROM center_extras WHERE id=? AND center_id=?',(eid,cid)).fetchone()
                        if not row: raise PermissionError('Extra no válido.')
                        db.execute('UPDATE center_extras SET name=?,description=?,price=?,active=?,updated_at=? WHERE id=?',(clean_text(data.get('name'),120),clean_text(data.get('description'),500),float(data.get('price') or 0),1 if data.get('active',1) else 0,now(),eid))
                    else:
                        db.execute('INSERT INTO center_extras(center_id,name,description,price,active,created_at,updated_at) VALUES(?,?,?,?,?,?,?)',(cid,clean_text(data.get('name'),120),clean_text(data.get('description'),500),float(data.get('price') or 0),1,now(),now()))
                    db.commit(); self.send_json({'ok':True}); return
                if path=='/api/center/extras/delete':
                    user=require_user(self,db); require_role(user,{'center','admin'}); data=json_body(self); cid=user['center_id'] if user['role']=='center' else int(data.get('center_id') or 0); eid=int(data.get('id') or 0); db.execute('DELETE FROM center_extras WHERE id=? AND center_id=?',(eid,cid)); db.commit(); self.send_json({'ok':True}); return
                if path=='/api/provider/reward-offers':
                    user=require_user(self,db); require_role(user,{'admin','center'})
                    if self.command == 'GET':
                        if user['role']=='admin':
                            rows=db.execute('SELECT ro.*, c.name AS center_name FROM reward_offers ro LEFT JOIN centers c ON c.id=ro.center_id ORDER BY ro.active DESC,ro.created_at DESC').fetchall()
                        else:
                            rows=db.execute('SELECT ro.*, c.name AS center_name FROM reward_offers ro LEFT JOIN centers c ON c.id=ro.center_id WHERE ro.center_id=? ORDER BY ro.active DESC,ro.created_at DESC',(user['center_id'],)).fetchall()
                        self.send_json({'items':[dict(r) for r in rows]}); return
                    data=json_body(self)
                    cid=int(data.get('center_id') or user.get('center_id') or 0)
                    if user['role']=='center' and cid!=user['center_id']: raise PermissionError('No puedes crear recompensas para otro centro.')
                    if not cid: raise ValueError('Selecciona un centro.')
                    if not db.execute('SELECT 1 FROM centers WHERE id=? AND active=1',(cid,)).fetchone(): raise ValueError('Centro no válido.')
                    title=clean_text(data.get('title'),180)
                    if not title: raise ValueError('El nombre de la recompensa es obligatorio.')
                    cur=db.execute('INSERT INTO reward_offers(center_id,title,description,reward_type,cost_wallet,value_text,conditions,stock,active,created_by_user_id,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,1,?,?,?)',(cid,title,clean_text(data.get('description'),1000),clean_text(data.get('reward_type'),50) or 'discount',max(0,float(data.get('cost_wallet') or 0)),clean_text(data.get('value_text'),180),clean_text(data.get('conditions'),1000),int(data['stock']) if str(data.get('stock','')).strip() else None,user['id'],now(),now())); audit(db,user['id'],'reward_offer_created','reward_offer',cur.lastrowid); db.commit(); self.send_json({'ok':True,'id':cur.lastrowid}); return
                self.send_json({'error':'Endpoint no encontrado'},404)
            except sqlite3.IntegrityError as e:
                db.rollback()  # never persist half-done work when a request fails
                self.send_json({'error':'El dato ya existe o no cumple una regla de integridad.','detail':str(e)},409)
            except (BrokenPipeError, ConnectionResetError):
                return
            except PermissionError as e:
                db.rollback()  # never persist half-done work when a request fails
                self.send_json({'error':str(e)},403)
            except ValueError as e:
                db.rollback()  # never persist half-done work when a request fails
                self.send_json({'error':str(e)},400)
            except KeyError as e:
                # A required field is missing in the request: the client's fault, not a server error.
                db.rollback()
                self.send_json({'error':f'Falta un dato obligatorio: {e.args[0] if e.args else ""}.'},400)
            except TypeError as e:
                db.rollback()
                log_exception(self, e)
                self.send_json({'error':'Algún dato enviado no tiene el formato esperado.'},400)
            except Exception as e:
                db.rollback()  # never persist half-done work when a request fails
                log_exception(self, e)
                payload={'error':'Error interno'}
                if os.environ.get('WOD_DEBUG','').strip().lower() in {'1','true','yes','on'}:
                    payload['detail']=str(e)
                self.send_json(payload,500)
            finally:
                invalidate_after_post(path)

    def do_DELETE(self):
        parsed=urlparse(self.path)
        if not self.precheck_write(): return
        if '/virtual/' in parsed.path and parsed.path.startswith('/api/dive-points/'):
            with connect() as db:
                try:
                    user=require_user(self,db); require_role(user,{'admin','center'})
                    parts=parsed.path.strip('/').split('/')
                    pid=int(parts[2]); vid=int(parts[4])
                    row=db.execute('SELECT v.media_path,p.center_id FROM virtual_experiences v JOIN dive_points p ON p.id=v.dive_point_id WHERE v.id=? AND v.dive_point_id=?',(vid,pid)).fetchone()
                    if not row: self.send_json({'error':'Recorrido no encontrado'},404); return
                    if user['role']=='center' and row['center_id']!=user['center_id']: raise PermissionError('No puedes eliminar este recorrido virtual.')
                    db.execute('UPDATE virtual_experiences SET active=0,updated_at=? WHERE id=?',(now(),vid)); audit(db,user['id'],'virtual_experience_deleted','virtual_experience',vid); db.commit(); self.send_json({'ok':True}); return
                except Exception as e: self.send_json({'error':str(e)},403 if isinstance(e,PermissionError) else 500)
            return
        if parsed.path.startswith('/api/dive-points/'):
            with connect() as db:
                try:
                    user=require_user(self,db); require_role(user,{'admin'}); pid=int(parsed.path.rsplit('/',1)[1]);
                    db.execute('UPDATE dive_points SET active=0,updated_at=? WHERE id=?',(now(),pid)); audit(db,user['id'],'dive_point_archived','dive_point',pid); db.commit(); self.send_json({'ok':True})
                except Exception as e: self.send_json({'error':str(e)},403 if isinstance(e,PermissionError) else 500)
            return
        self.send_json({'error':'Endpoint no encontrado'},404)

    def login_user(self, uid, db=None, payload=None):
        """Create a persistent session and answer the request (one response only)."""
        token=secrets.token_urlsafe(32); now_ts=time.time(); token_hash=hashlib.sha256(token.encode()).hexdigest()
        own = db is None
        conn = connect() if own else db
        try:
            conn.execute('DELETE FROM sessions WHERE last_seen<?',(now_ts-SESSION_TTL_SECONDS,))
            conn.execute('INSERT INTO sessions(token_hash,user_id,created_at,last_seen) VALUES(?,?,?,?)',(token_hash,uid,now_ts,now_ts)); conn.commit()
        finally:
            if own: conn.close()
        secure = '; Secure' if os.environ.get('WOD_SECURE_COOKIES','').strip().lower() in {'1','true','yes','on'} or os.environ.get('WOD_PUBLIC_URL','').lower().startswith('https://') else ''
        body=json.dumps(payload or {'ok':True},ensure_ascii=False).encode('utf-8')
        self.send_response(200); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Set-Cookie',f'{COOKIE}={token}; Path=/; HttpOnly; SameSite=Lax{secure}'); self.send_header('Content-Length',str(len(body))); self.send_header('Cache-Control','no-store'); self.security_headers(); self.end_headers(); self.wfile.write(body)

    def logout_user(self):
        cookie=self.headers.get('Cookie',''); token=None
        for item in cookie.split(';'):
            k,_,v=item.strip().partition('=')
            if k==COOKIE: token=v
        if token:
            with connect() as conn:
                conn.execute('DELETE FROM sessions WHERE token_hash=?',(hashlib.sha256(token.encode()).hexdigest(),)); conn.commit()
        secure = '; Secure' if os.environ.get('WOD_SECURE_COOKIES','').strip().lower() in {'1','true','yes','on'} or os.environ.get('WOD_PUBLIC_URL','').lower().startswith('https://') else ''
        body=b'{"ok":true}'
        self.send_response(200); self.send_header('Content-Type','application/json'); self.send_header('Set-Cookie',f'{COOKIE}=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax{secure}'); self.send_header('Content-Length',str(len(body))); self.security_headers(); self.end_headers(); self.wfile.write(body)


class WorldivesHTTPServer(ThreadingHTTPServer):
    allow_reuse_port = False

    def server_bind(self):
        if self.allow_reuse_port and hasattr(socket,'SO_REUSEPORT'):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        super().server_bind()

    # Python's default accept backlog is 5: with many simultaneous visitors extra connections were reset.
    request_queue_size = int(os.environ.get('WOD_BACKLOG', '1024'))
    daemon_threads = True
    # At most this many requests are processed at once per process. Beyond that, new connections
    # wait in the kernel queue instead of spawning thousands of threads that fight for the CPU
    # (measured: unbounded threads made every request slow when traffic exceeded capacity).
    max_concurrent = int(os.environ.get('WOD_MAX_CONCURRENT', '64'))

    def server_activate(self):
        super().server_activate()
        self._slots = threading.BoundedSemaphore(self.max_concurrent)

    def process_request(self, request, client_address):
        self._slots.acquire()
        try:
            super().process_request(request, client_address)
        except BaseException:
            self._slots.release(); raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self._slots.release()


def maintenance_loop():
    """Every 10 minutes: expired sessions are deleted (they are already refused when used). Further periodic jobs
    (booking deadlines, retention, backups) are registered in MAINTENANCE_JOBS by later modules."""
    while True:
        db = None
        try:
            db = connect()
            db.execute('DELETE FROM sessions WHERE last_seen<? OR created_at<?', (time.time() - SESSION_TTL_SECONDS, time.time() - SESSION_TTL_SECONDS))
            db.commit()
            for job in MAINTENANCE_JOBS:
                try: job(db); db.commit()
                except Exception as exc:
                    db.rollback(); sys.stderr.write(f'[mantenimiento] {getattr(job, "__name__", job)}: {type(exc).__name__}: {exc}\n')
        except Exception as exc:
            sys.stderr.write(f'[mantenimiento] {type(exc).__name__}: {exc}\n')
        finally:
            if db is not None: db.close()
        time.sleep(wcfg.env_int('WOD_MAINTENANCE_SECONDS', 60, 5, 3600))


MAINTENANCE_JOBS = [run_booking_deadlines, run_refund_reminders]


def check_production_settings():
    """WOD_ENV=production refuses to start with unsafe settings."""
    problems = []
    if not wcfg.public_url(): problems.append('WOD_PUBLIC_URL es obligatorio en producción (por ejemplo https://worldives.com).')
    elif not wcfg.public_url().startswith('https://'): problems.append('WOD_PUBLIC_URL debe empezar por https:// en producción.')
    if wcfg.env_flag('WOD_ALLOW_SETUP'): problems.append('WOD_ALLOW_SETUP=1 no se permite en producción: crea el administrador con --create-admin.')
    if len(wcfg.env('WOD_SECRET_KEY')) < 32: problems.append('Define WOD_SECRET_KEY con al menos 32 caracteres aleatorios.')
    if wcfg.env_flag('WOD_DEBUG'): problems.append('WOD_DEBUG no puede estar activo en producción.')
    return problems


def create_admin_cli(argv):
    """python app/server.py --create-admin [--email E] [--username U] [--name N]
    The password is asked on the terminal (or read from WOD_ADMIN_PASSWORD for automated installs)."""
    import getpass
    def arg(flag):
        if flag in argv:
            i = argv.index(flag)
            if i + 1 < len(argv): return argv[i + 1]
        return None
    bootstrap()
    email = (arg('--email') or input('Email del administrador: ')).strip().lower()
    username = (arg('--username') or input('Usuario: ')).strip()
    name = (arg('--name') or input('Nombre y apellidos: ')).strip()
    password = os.environ.get('WOD_ADMIN_PASSWORD') or getpass.getpass('Contraseña (mínimo 10 caracteres): ')
    if not os.environ.get('WOD_ADMIN_PASSWORD') and getpass.getpass('Repite la contraseña: ') != password:
        print('Las contraseñas no coinciden.'); return 1
    problem = wsec.password_problem(password)
    if problem: print(problem); return 1
    if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email) or not username or not name:
        print('Email, usuario y nombre son obligatorios.'); return 1
    db = connect()
    try:
        if db.execute('SELECT 1 FROM users WHERE lower(email)=? OR lower(username)=lower(?)', (email, username)).fetchone():
            print('Ya existe una cuenta con ese email o usuario.'); return 1
        uid = db.execute("INSERT INTO users(fullname,email,username,password_hash,role,requested_role,created_at,email_verified_at) VALUES(?,?,?,?,'admin','admin',?,?)",
                         (name, email, username, hash_password(password), now(), now())).lastrowid
        db.execute('INSERT OR IGNORE INTO user_profiles(user_id,updated_at) VALUES(?,?)', (uid, now()))
        record_acceptances(db, uid, ['terminos', 'privacidad', 'centros'])
        audit(db, uid, 'admin_created_cli', 'user', uid); db.commit()
    finally:
        db.close()
    print(f'Administrador creado: {username} <{email}>. Entra en la web y activa la verificación en dos pasos.')
    return 0


def report_center_accounts():
    """python app/server.py --report-center-accounts: how every centre/freelance account got its role (G2 review)."""
    bootstrap()
    db = connect()
    try:
        rows = db.execute("SELECT u.id,u.fullname,u.email,u.role,u.center_id,u.created_at,c.name AS center FROM users u LEFT JOIN centers c ON c.id=u.center_id WHERE u.role IN ('center','freelance') ORDER BY u.id").fetchall()
        print(f'Cuentas profesionales: {len(rows)}')
        for u in rows:
            reg = db.execute("SELECT details,created_at FROM audit_log WHERE action='register' AND entity_id=? ORDER BY id LIMIT 1", (u['id'],)).fetchone()
            claim = db.execute('SELECT status,verification_method,reviewed_by_user_id FROM center_claims WHERE user_id=? ORDER BY id DESC LIMIT 1', (u['id'],)).fetchone()
            how = 'aprobada por el administrador (' + (claim['verification_method'] or 'sin método registrado') + ')' if claim and claim['status'] == 'approved' else 'SIN aprobación registrada: revisar'
            print(f"- #{u['id']} {u['fullname']} <{u['email']}> rol={u['role']} centro={u['center'] or '-'} alta={u['created_at']} · {how} · registro: {reg['details'] if reg else 'sin registro'}")
        orphan = db.execute("SELECT id,center_id,requested_center_name,status FROM center_claims WHERE user_id NOT IN (SELECT id FROM users)").fetchall()
        for c in orphan: print(f"- Solicitud #{c['id']} «{c['requested_center_name']}» sin cuenta asociada (estado {c['status']}).")
        legacy = db.execute("SELECT entity_id,details,created_at FROM audit_log WHERE action='register' AND details LIKE '%\"requested_role\": \"center\"%'").fetchall()
        for a in legacy: print(f"- Registro histórico como centro (usuario #{a['entity_id'] or '?'}, {a['created_at']}): {a['details']}")
    finally:
        db.close()
    return 0


def main():
    if '--create-admin' in sys.argv: raise SystemExit(create_admin_cli(sys.argv))
    if '--report-center-accounts' in sys.argv: raise SystemExit(report_center_accounts())
    if wcfg.is_production():
        problems = check_production_settings()
        if problems:
            print('No se puede arrancar en producción:'); [print(' - ' + p) for p in problems]; raise SystemExit(2)
    bootstrap()
    print(f'WORLDIVES DISCOVERY v{APP_VERSION} -> http://127.0.0.1:{PORT}')
    # Optional multi-process mode (Linux/macOS): WOD_WORKERS=4 starts 4 processes sharing the port.
    # Sessions live in the database, so any process can serve any user.
    workers=max(1,int(os.environ.get('WOD_WORKERS','1') or 1))
    reuse=workers>1 and hasattr(os,'fork') and hasattr(socket,'SO_REUSEPORT')
    if workers>1 and not reuse: print('WOD_WORKERS solo está disponible en Linux/macOS; se usa un único proceso.')
    if reuse:
        WorldivesHTTPServer.allow_reuse_port=True
        for _ in range(workers-1):
            if os.fork()==0: break
    try:
        s=WorldivesHTTPServer((HOST,PORT),Handler)
    except OSError as e:
        print(f'No se puede abrir el puerto {PORT}: {e}')
        raise
    threading.Thread(target=warm_snapshots, name='warm-up', daemon=True).start()
    threading.Thread(target=sweep_payment_orders, name='payments-sweeper', daemon=True).start()
    # Only one process (WOD_WORKERS may start several) sends emails and runs the periodic jobs.
    is_worker = email_worker_lock()
    if is_worker: threading.Thread(target=maintenance_loop, name='maintenance', daemon=True).start()
    if is_worker: threading.Thread(target=email_scheduler, name='email-sender', daemon=True).start()
    s.serve_forever()


_MAIL_LOCK = None
def email_worker_lock():
    """Only one process sends emails and runs the hourly jobs (WOD_WORKERS may start several)."""
    global _MAIL_LOCK
    try:
        import fcntl
        _MAIL_LOCK = open(DATA / '.email-worker.lock', 'w')
        fcntl.flock(_MAIL_LOCK, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except ImportError:
        return True
    except OSError:
        return False


def warm_snapshots():
    """Build the public catalogue snapshots as soon as the process starts, so the first visitors do not wait."""
    db=None
    try:
        db=connect()
        for snap in (POINTS, DIRECTORY, DIVE_TYPES, TRAVEL, SITE_MEDIA, PROMOS): snap.get(db)
    except Exception as e:
        sys.stderr.write(f'[warm-up] {type(e).__name__}: {e}\n')
    finally:
        if db is not None: db.close()

if __name__=='__main__':
    main()
