"""Booking modes and the booking state machine (Fase 1B).

Two booking modes per service (the old «Reserva inmediata» no longer exists):
  payment  «Pago al reservar · confirmación inmediata»: the diver pays to book; the booking confirms itself when
           Stripe confirms the payment. Only for providers with online payments active.
  request  «Bajo petición · el centro responde en X h»: the diver sends a request without paying; the centre
           accepts or rejects within its deadline; if it accepts and charges online, the diver pays within a deadline.

One set of states, used by the server, the panel, «Mis reservas», the emails and the PDFs. The identifiers are
stored in English (as the rest of the database); the labels are the official Spanish names:

  requested                 solicitada                 request sent, no spots taken, no money
  accepted_pending_payment  aceptada_pendiente_pago    centre accepted, spots held, waiting for the diver's payment
  payment_in_progress       pago_en_curso              «Pago al reservar»: spots held for a few minutes while the diver pays
  insurance_pending         falta_seguro               v50.56: the service asks for a diving insurance «obligatorio para reservar
                                                       online» and the diver has none for that day: spots held while he uploads it
  confirmed                 confirmada                 the place is the diver's (paid, free, or pay at the centre)
  rejected                  rechazada                  the centre said no
  expired                   caducada                   a deadline passed (no answer, no payment, payment abandoned)
  cancelled                 cancelada                  cancelled by the diver or the centre
  completed                 completada                 the activity took place
"""
from __future__ import annotations

from datetime import datetime, timedelta

MODES = ('payment', 'request')
MODE_LABELS = {
    'payment': 'Pago al reservar · confirmación inmediata',
    'request': 'Bajo petición · el centro responde en {hours} h',
}

STATES = {
    'requested': 'Solicitada',
    'accepted_pending_payment': 'Aceptada · pendiente de pago',
    'payment_in_progress': 'Pago en curso',
    'insurance_pending': 'Falta el seguro',
    'confirmed': 'Confirmada',
    'rejected': 'Rechazada',
    'expired': 'Caducada',
    'cancelled': 'Cancelada',
    'completed': 'Completada',
}
STATE_CODES_ES = {
    'requested': 'solicitada', 'accepted_pending_payment': 'aceptada_pendiente_pago', 'payment_in_progress': 'pago_en_curso',
    'insurance_pending': 'falta_seguro', 'confirmed': 'confirmada', 'rejected': 'rechazada', 'expired': 'caducada', 'cancelled': 'cancelada', 'completed': 'completada',
}
# Legacy identifiers still found in old rows or old clients.
LEGACY = {'pending': 'requested', 'unpaid': 'expired'}

# States that hold spots in a departure.
HOLDING = ('accepted_pending_payment', 'payment_in_progress', 'insurance_pending', 'confirmed')
# Not a booking yet (the centre does not see it, the spots are only held): the payment or the insurance is missing.
PRE_BOOKING = ('payment_in_progress', 'insurance_pending')
# States a centre sees as a real booking in its lists and planning (payment_in_progress only as a grey «pago en curso»).
VISIBLE_TO_CENTER = ('requested', 'accepted_pending_payment', 'confirmed', 'completed', 'cancelled', 'rejected')
# Final states.
FINAL = ('rejected', 'expired', 'cancelled', 'completed')
# A diver can cancel these.
CANCELLABLE = ('requested', 'accepted_pending_payment', 'confirmed')

DEFAULT_RESPONSE_HOURS = 24
DEFAULT_PAYMENT_HOURS = 24
DEFAULT_HOLD_MINUTES = 10   # v50.56 (motor multicanal): 10 minutes by default, WOD_PAYMENT_HOLD_MINUTES changes it
DEFAULT_INSURANCE_HOLD_MINUTES = 60   # v50.56 (seguros): time to contract and upload the insurance, WOD_INSURANCE_HOLD_MINUTES
MIN_RESPONSE_HOURS = 1
MAX_RESPONSE_HOURS = 168


def normalize_state(state: str | None) -> str:
    s = (state or '').strip()
    return LEGACY.get(s, s)


def state_label(state: str | None) -> str:
    s = normalize_state(state)
    return STATES.get(s, s or '—')


def mode_label(mode: str | None, response_hours: int | None = None) -> str:
    m = 'payment' if mode == 'payment' else 'request'
    return MODE_LABELS[m].format(hours=int(response_hours or DEFAULT_RESPONSE_HOURS))


def clamp_hours(value, default: int) -> int:
    try:
        v = int(float(value))
    except (TypeError, ValueError):
        return default
    return max(MIN_RESPONSE_HOURS, min(MAX_RESPONSE_HOURS, v))


def activity_start(booking_date: str | None, booking_time: str | None) -> datetime | None:
    try:
        t = (booking_time or '09:00')[:5]
        if len(t) != 5 or t[2] != ':':
            t = '09:00'
        return datetime.fromisoformat(f'{booking_date}T{t}')
    except Exception:
        return None


def deadline_before_start(now_local: datetime, hours: int, start: datetime | None) -> datetime:
    """now + hours, but never later than the start of the activity (deadline rule of Fase 1B)."""
    d = now_local + timedelta(hours=hours)
    if start and d > start:
        d = start
    return d
