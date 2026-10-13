"""What the professional app (Centro PRO and Freelance PRO, v50.49) needs that has no database: the code of a
booking that a diver can read aloud, reading the QR of a booking, and the WhatsApp texts in the client's language.
"""
import re
from urllib.parse import quote

# A booking QR: {base}/#/verificarreserva?id=<id>&t=<long random token>. Read aloud: «1234-A1B2C3» (id and the first six
# characters of the token). Nothing else is accepted.
_URL = re.compile(r'verificarreserva\?(?:[^#\s]*&)?id=(\d{1,10})&t=([0-9A-Za-z_\-]{8,128})')
_URL2 = re.compile(r'verificarreserva\?(?:[^#\s]*&)?t=([0-9A-Za-z_\-]{8,128})&id=(\d{1,10})')
_SHORT = re.compile(r'(?:WOD-?)?0*(\d{1,10})\s*[-\s·.]\s*([0-9A-Za-z]{6})')


def booking_code(booking_id, token):
    return f"{int(booking_id)}-{str(token or '')[:6].upper()}" if token else str(int(booking_id))


def parse_code(raw):
    """(booking id, token or 6-character prefix, 'qr'|'code') or None."""
    s = str(raw or '').strip()[:400]
    m = _URL.search(s)
    if m: return int(m.group(1)), m.group(2), 'qr'
    m = _URL2.search(s)
    if m: return int(m.group(2)), m.group(1), 'qr'
    m = _SHORT.fullmatch(s.upper())
    if m: return int(m.group(1)), m.group(2), 'code'
    return None


def token_matches(stored, given, how):
    import hmac
    stored = str(stored or ''); given = str(given or '')
    if not stored or not given: return False
    if how == 'qr': return hmac.compare_digest(stored, given)
    return hmac.compare_digest(stored[:6].upper(), given.upper())


# WhatsApp from the professional's own phone (a wa.me link the app opens): the text goes in the client's language.
WA_TEXTS = {
    'reserva': {
        'es': ('Hola {name}, te escribimos de {center} por tu reserva de {service} del {date} a las {time}.', 'Hola {name}, te escribimos de {center} por tu reserva de {service} del {date}.'),
        'en': ('Hi {name}, this is {center} about your {service} booking on {date} at {time}.', 'Hi {name}, this is {center} about your {service} booking on {date}.'),
        'fr': ('Bonjour {name}, ici {center} au sujet de votre réservation {service} du {date} à {time}.', 'Bonjour {name}, ici {center} au sujet de votre réservation {service} du {date}.'),
        'de': ('Hallo {name}, hier ist {center} wegen deiner Buchung {service} am {date} um {time}.', 'Hallo {name}, hier ist {center} wegen deiner Buchung {service} am {date}.'),
        'it': ('Ciao {name}, ti scriviamo da {center} per la tua prenotazione di {service} del {date} alle {time}.', 'Ciao {name}, ti scriviamo da {center} per la tua prenotazione di {service} del {date}.'),
        'pt': ('Olá {name}, escrevemos de {center} sobre a sua reserva de {service} no dia {date} às {time}.', 'Olá {name}, escrevemos de {center} sobre a sua reserva de {service} no dia {date}.'),
        'nl': ('Hallo {name}, je krijgt dit bericht van {center} over je boeking {service} op {date} om {time}.', 'Hallo {name}, je krijgt dit bericht van {center} over je boeking {service} op {date}.'),
        'pl': ('Dzień dobry {name}, piszemy z {center} w sprawie rezerwacji {service} w dniu {date} o {time}.', 'Dzień dobry {name}, piszemy z {center} w sprawie rezerwacji {service} w dniu {date}.'),
        'zh': ('{name}您好，我们是{center}，关于您{date} {time}的{service}预订。', '{name}您好，我们是{center}，关于您{date}的{service}预订。'),
    },
    'pago': {
        'es': ('Hola {name}, tu plaza de {service} del {date} a las {time} está aceptada. Para confirmarla, completa el pago aquí: {link}', 'Hola {name}, tu plaza de {service} del {date} está aceptada. Para confirmarla, completa el pago aquí: {link}'),
        'en': ('Hi {name}, your place for {service} on {date} at {time} has been accepted. To confirm it, please complete the payment here: {link}', 'Hi {name}, your place for {service} on {date} has been accepted. To confirm it, please complete the payment here: {link}'),
        'fr': ('Bonjour {name}, votre place pour {service} du {date} à {time} est acceptée. Pour la confirmer, finalisez le paiement ici : {link}', 'Bonjour {name}, votre place pour {service} du {date} est acceptée. Pour la confirmer, finalisez le paiement ici : {link}'),
        'de': ('Hallo {name}, dein Platz für {service} am {date} um {time} ist bestätigt. Bitte schließe die Zahlung hier ab: {link}', 'Hallo {name}, dein Platz für {service} am {date} ist bestätigt. Bitte schließe die Zahlung hier ab: {link}'),
        'it': ('Ciao {name}, il tuo posto per {service} del {date} alle {time} è stato accettato. Per confermarlo, completa il pagamento qui: {link}', 'Ciao {name}, il tuo posto per {service} del {date} è stato accettato. Per confermarlo, completa il pagamento qui: {link}'),
        'pt': ('Olá {name}, o seu lugar em {service} no dia {date} às {time} foi aceite. Para o confirmar, conclua o pagamento aqui: {link}', 'Olá {name}, o seu lugar em {service} no dia {date} foi aceite. Para o confirmar, conclua o pagamento aqui: {link}'),
        'nl': ('Hallo {name}, je plek voor {service} op {date} om {time} is geaccepteerd. Rond de betaling hier af om hem te bevestigen: {link}', 'Hallo {name}, je plek voor {service} op {date} is geaccepteerd. Rond de betaling hier af om hem te bevestigen: {link}'),
        'pl': ('Dzień dobry {name}, Twoje miejsce na {service} w dniu {date} o {time} zostało przyjęte. Aby je potwierdzić, dokończ płatność tutaj: {link}', 'Dzień dobry {name}, Twoje miejsce na {service} w dniu {date} zostało przyjęte. Aby je potwierdzić, dokończ płatność tutaj: {link}'),
        'zh': ('{name}您好，您{date} {time}的{service}名额已确认接受。请在此完成付款以确认：{link}', '{name}您好，您{date}的{service}名额已确认接受。请在此完成付款以确认：{link}'),
    },
}
LANGS = ('es', 'en', 'fr', 'de', 'it', 'pt', 'nl', 'pl', 'zh')


def wa_text(kind, lang, **kw):
    kind = kind if kind in WA_TEXTS else 'reserva'
    lang = lang if lang in LANGS else 'en'
    with_time, without = WA_TEXTS[kind][lang]
    tpl = with_time if kw.get('time') else without
    return tpl.format(**{k: (v or '') for k, v in kw.items()})


def wa_url(e164, text):
    digits = re.sub(r'\D', '', str(e164 or ''))
    return f'https://wa.me/{digits}?text={quote(text)}' if digits else None
