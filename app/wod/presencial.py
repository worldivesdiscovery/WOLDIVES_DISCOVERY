"""v50.55 · «Pago en persona» (encargo del 15/10/2026): a freelance professional is paid directly by the client (cash,
Bizum, bank transfer…), never through WORLDIVES. For these services WORLDIVES is only the search, the showcase and the
agenda: no Stripe, no deposit, no refunds and no managed cancellation policy.

Here: the pure rules and texts (no database). The routes, the storage and the e-mails are in server.py.

- The client always sends a request («Bajo petición»): «Pago al reservar» is not possible.
- The price is the one published, computed by the same quote as every other booking, and kept on the booking.
- The professional's WhatsApp is never public: the client gets the button «Hablar por WhatsApp» only once the
  professional has accepted.
- The professional may mark «Cobrado» or «No se presentó» on a booking, only for his own records.

Texts marked PENDIENTE ABOGADO are a base text waiting for the lawyer's review."""
from __future__ import annotations

import re
from urllib.parse import quote

WAYS = ('online', 'in_person')
WAY_LABELS = {'online': 'Pago online', 'in_person': 'Pago en persona'}
METHODS = ('cash', 'bizum', 'transfer', 'other')
METHOD_LABELS = {'cash': 'Efectivo', 'bizum': 'Bizum', 'transfer': 'Transferencia', 'other': 'Otra'}
OTHER_MAX = 40
POLICY_MAX = 1000
MARKS = ('paid', 'no_show')
MARK_LABELS = {'paid': 'Cobrado', 'no_show': 'No se presentó'}

LABEL = 'Pago en persona al profesional'
CONFIRMED_LABEL = 'Confirmada · pago en persona'
POLICY_TITLE = 'Política del profesional'
PRICE_LABEL = 'Precio publicado'
# PENDIENTE ABOGADO: base text of the notice the client accepts before sending the request (brief of 15/10/2026).
NOTICE = ('Este profesional cobra directamente, no a través de WORLDIVES. El precio es el publicado aquí. Acuerda con él '
          'la forma de pago y los detalles por WhatsApp. En este servicio WORLDIVES no gestiona pagos, devoluciones, '
          'cancelaciones ni incidencias.')
NOTICE_VERSION = '2026-10-15'
ACK_LABEL = 'He leído el aviso: pago en persona al profesional'
TERMS_DOC = 'pago-en-persona'      # app/legal/<lang>/pago-en-persona.md: what the professional accepts when activating it


def clean_methods(raw, other) -> tuple[list[str], str]:
    """The ways of paying the professional accepts (informative): at least one; «Otra» needs a short text."""
    if isinstance(raw, str): raw = [x for x in re.split(r'[,\s]+', raw) if x]
    if not isinstance(raw, (list, tuple)): raw = []
    methods = [m for m in METHODS if m in raw]
    if not methods: raise ValueError('Marca al menos una forma de pago que aceptas: efectivo, Bizum, transferencia u otra.')
    text = re.sub(r'\s+', ' ', str(other or '')).strip()
    if 'other' in methods:
        if not text: raise ValueError('Escribe cuál es la otra forma de pago (por ejemplo, «Tarjeta en mano»).')
        if len(text) > OTHER_MAX: raise ValueError(f'La otra forma de pago admite como mucho {OTHER_MAX} caracteres.')
    else:
        text = ''
    return methods, text


def clean_policy(text) -> str:
    """The professional's own cancellation policy (free text, optional), shown as «Política del profesional»."""
    t = re.sub(r'[ \t]+', ' ', str(text or '')).strip()
    if len(t) > POLICY_MAX: raise ValueError(f'Tu política de cancelación admite como mucho {POLICY_MAX} caracteres.')
    return t


def methods_text(methods, other='') -> str:
    """«Efectivo · Bizum · Tarjeta en mano» (Spanish; the web and the e-mails translate each word)."""
    out = [METHOD_LABELS[m] for m in (methods or []) if m in METHOD_LABELS and m != 'other']
    if other and 'other' in (methods or []): out.append(other)
    return ' · '.join(out)


# The message the client's WhatsApp opens with (wa.me): service, date and booking number, in the client's language.
WA_MESSAGE = {
    'es': 'Hola, te escribo por mi reserva nº {n} en WORLDIVES: «{service}», {date}. ¿Cómo prefieres que te pague?',
    'en': 'Hello, I am writing about my booking no. {n} on WORLDIVES: “{service}”, {date}. How would you like me to pay?',
    'fr': 'Bonjour, je vous écris au sujet de ma réservation n° {n} sur WORLDIVES : « {service} », {date}. Comment préférez-vous que je vous paie ?',
    'de': 'Hallo, ich schreibe wegen meiner Buchung Nr. {n} bei WORLDIVES: „{service}“, {date}. Wie soll ich bezahlen?',
    'it': 'Ciao, ti scrivo per la mia prenotazione n. {n} su WORLDIVES: «{service}», {date}. Come preferisci che ti paghi?',
    'pt': 'Olá, escrevo-te sobre a minha reserva n.º {n} no WORLDIVES: «{service}», {date}. Como preferes que te pague?',
    'pl': 'Dzień dobry, piszę w sprawie mojej rezerwacji nr {n} w WORLDIVES: „{service}”, {date}. Jak mam zapłacić?',
    'nl': 'Hallo, ik schrijf over mijn boeking nr. {n} op WORLDIVES: “{service}”, {date}. Hoe wil je dat ik betaal?',
    'zh': '你好，我想咨询我在 WORLDIVES 的预订（编号 {n}）：「{service}」，{date}。请问你希望我如何付款？',
}


def wa_message(lang, number, service, date) -> str:
    return WA_MESSAGE.get(lang or 'es', WA_MESSAGE['es']).format(n=number, service=service or '', date=date or '')


def wa_link(e164, text) -> str:
    """https://wa.me/<digits>?text=… (empty without a valid number)."""
    digits = re.sub(r'\D', '', str(e164 or ''))
    if len(digits) < 8: return ''
    return f'https://wa.me/{digits}?text={quote(text or "")}'
