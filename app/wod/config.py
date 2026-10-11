"""Settings read from environment variables. Every variable is documented in .env.example."""
from __future__ import annotations

import os
from pathlib import Path


def load_env_file(path: Path | None = None) -> int:
    """Reads the server's .env (WOD_ENV_FILE, or .env next to the application) into the environment.
    Variables already set (systemd, shell, tests) win. Supports «KEY=value  # comment», quotes and blank lines.
    Returns how many variables were loaded."""
    p = Path(os.environ.get('WOD_ENV_FILE') or path or (Path(__file__).resolve().parents[2] / '.env'))
    if not p.is_file():
        return 0
    n = 0
    for raw in p.read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, _, value = line.partition('=')
        key = key.strip().removeprefix('export ').strip()
        value = value.strip()
        if value[:1] in ('"', "'") and value[1:].find(value[0]) >= 0:
            value = value[1:1 + value[1:].find(value[0])]
        else:
            cut = value.find(' #')
            if cut >= 0: value = value[:cut]
            value = value.strip()
        if key and key not in os.environ:
            os.environ[key] = value; n += 1
    return n


if not os.environ.get('WOD_NO_ENV_FILE'):
    load_env_file()


def env(name: str, default: str = '') -> str:
    return (os.environ.get(name, default) or '').strip()


def env_flag(name: str, default: bool = False) -> bool:
    v = env(name)
    if not v:
        return default
    return v.lower() in {'1', 'true', 'yes', 'on', 'si', 'sí'}


def env_int(name: str, default: int, minimum: int | None = None, maximum: int | None = None) -> int:
    try:
        v = int(env(name, str(default)) or default)
    except ValueError:
        v = default
    if minimum is not None:
        v = max(minimum, v)
    if maximum is not None:
        v = min(maximum, v)
    return v


def environment() -> str:
    """'production', 'staging', 'demo' or 'development' (default)."""
    v = env('WOD_ENV', 'development').lower()
    return v if v in {'production', 'staging', 'demo', 'development'} else 'development'


def is_production() -> bool:
    return environment() == 'production'


def demo_mode() -> bool:
    """Demo deployments: banner, no real payments, no open registration, noindex."""
    return env_flag('WOD_DEMO_MODE') or environment() == 'demo'


def public_url() -> str:
    return env('WOD_PUBLIC_URL').rstrip('/')


# Request size limits (G7)
MAX_JSON_BYTES = env_int('WOD_MAX_JSON_BYTES', 1024 * 1024, 16 * 1024, 8 * 1024 * 1024)
MAX_UPLOAD_BYTES = env_int('WOD_MAX_UPLOAD_MB', 15, 1, 100) * 1024 * 1024
MAX_DOCUMENT_BYTES = env_int('WOD_MAX_DOCUMENT_MB', 10, 1, 50) * 1024 * 1024
MAX_VIRTUAL_UPLOAD_BYTES = env_int('WOD_MAX_VIRTUAL_UPLOAD_MB', 15, 1, 100) * 1024 * 1024
MAX_WEBHOOK_BYTES = 1024 * 1024

# Passwords and sessions
PBKDF2_ITERATIONS = env_int('WOD_PBKDF2_ITERATIONS', 600_000, 100_000, 5_000_000)

# Embeds allowed in virtual tours (G3). Host suffix + optional path prefix.
DEFAULT_EMBED_DOMAINS = 'youtube-nocookie.com,player.vimeo.com,google.com/maps'


def embed_domains() -> list[str]:
    raw = env('WOD_EMBED_DOMAINS', DEFAULT_EMBED_DOMAINS)
    return [x.strip().lower() for x in raw.split(',') if x.strip()]
