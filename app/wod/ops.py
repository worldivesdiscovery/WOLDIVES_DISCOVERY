"""Operations: access log with daily rotation and a fixed retention, and an alert when 500 errors repeat."""
from __future__ import annotations

import logging
import logging.handlers
import sys
import threading
import time
from pathlib import Path

from . import config


def access_logger(log_dir: Path) -> logging.Logger:
    """Access log without query strings and with truncated IPs (see wod.security.log_ip).
    File logs/access.log rotated every midnight; WOD_LOG_RETENTION_DAYS (14 by default) files are kept.
    WOD_ACCESS_LOG=stdout writes to the console instead (useful under systemd/journald, which rotates by itself);
    WOD_ACCESS_LOG=off disables it."""
    log = logging.getLogger('wod.access')
    if log.handlers:
        return log
    log.propagate = False
    log.setLevel(logging.INFO)
    mode = config.env('WOD_ACCESS_LOG', 'file').lower()
    if mode == 'off':
        log.addHandler(logging.NullHandler())
        return log
    if mode == 'stdout':
        h = logging.StreamHandler(sys.stdout)
    else:
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            h = logging.handlers.TimedRotatingFileHandler(log_dir / 'access.log', when='midnight', backupCount=config.env_int('WOD_LOG_RETENTION_DAYS', 14, 1, 365), encoding='utf-8')
        except OSError:
            h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter('%(asctime)s %(message)s', '%Y-%m-%dT%H:%M:%S'))
    log.addHandler(h)
    return log


class ErrorMonitor:
    """Counts unexpected errors (HTTP 500). When WOD_ALERT_ERRORS (5) happen within WOD_ALERT_WINDOW_MIN (10)
    minutes, `on_alert` is called once (the server queues an email to the administrators). Then it stays quiet
    for an hour so a broken deployment does not flood the inbox."""

    def __init__(self, on_alert=None):
        self.on_alert = on_alert
        self.threshold = config.env_int('WOD_ALERT_ERRORS', 5, 1)
        self.window = config.env_int('WOD_ALERT_WINDOW_MIN', 10, 1) * 60
        self._lock = threading.Lock()
        self._events: list[tuple[float, str]] = []
        self._last_alert = 0.0

    def record(self, path: str, exc: BaseException):
        current = time.time()
        fire = None
        with self._lock:
            self._events = [e for e in self._events if current - e[0] < self.window]
            self._events.append((current, f'{path}: {type(exc).__name__}: {exc}'[:300]))
            if len(self._events) >= self.threshold and current - self._last_alert > 3600:
                self._last_alert = current
                fire = list(self._events)
        if fire and self.on_alert:
            try:
                self.on_alert(fire)
            except Exception as e:  # never let the alert break a request
                sys.stderr.write(f'[alertas] {e}\n')

    def recent(self):
        with self._lock:
            return list(self._events)
