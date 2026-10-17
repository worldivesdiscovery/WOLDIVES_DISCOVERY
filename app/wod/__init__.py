"""WORLDIVES DISCOVERY: reusable building blocks shared by the HTTP server (app/server.py).

Each module holds one concern so it can be tested on its own:
  config    - settings read from the environment (one place, documented in .env.example)
  security  - passwords, rate limits, client IP behind a proxy, URL and file checks, CSP
  bookings  - booking modes, the booking state machine and its deadlines
  points    - the WORLDIVES points programme (earned, never bought, never money)
  plans     - subscription plans and feature switches for centres
  totp      - optional two-step verification (RFC 6238)
"""
