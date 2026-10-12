"""Dates and amounts written for people, in their language (e-mails, PDF, texts): «domingo, 11 de octubre de 2026»,
«Sunday 11 October 2026», «1 234,50 €»… v50.46: separated from app/server.py (plan of docs/estructura.md).
Pure functions without the database."""
from __future__ import annotations

import datetime as _dt
from datetime import datetime

ES_MONTHS = ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre']
ES_DAYS = ['lunes','martes','miércoles','jueves','viernes','sábado','domingo']


def es_long_date(value):
    try:
        d=_dt.date.fromisoformat(str(value)[:10]); return f'{ES_DAYS[d.weekday()]}, {d.day} de {ES_MONTHS[d.month-1]} de {d.year}'
    except Exception: return str(value or '')


_MONTHS = {
    'en': ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
    'fr': ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'],
    'de': ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'],
    'it': ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre'],
    'pt': ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'],
    'nl': ['januari', 'februari', 'maart', 'april', 'mei', 'juni', 'juli', 'augustus', 'september', 'oktober', 'november', 'december'],
    'pl': ['stycznia', 'lutego', 'marca', 'kwietnia', 'maja', 'czerwca', 'lipca', 'sierpnia', 'września', 'października', 'listopada', 'grudnia']}
_DAYS = {
    'en': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
    'fr': ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche'],
    'de': ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag'],
    'it': ['lunedì', 'martedì', 'mercoledì', 'giovedì', 'venerdì', 'sabato', 'domenica'],
    'pt': ['segunda-feira', 'terça-feira', 'quarta-feira', 'quinta-feira', 'sexta-feira', 'sábado', 'domingo'],
    'nl': ['maandag', 'dinsdag', 'woensdag', 'donderdag', 'vrijdag', 'zaterdag', 'zondag'],
    'zh': ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日'],
    'pl': ['poniedziałek', 'wtorek', 'środa', 'czwartek', 'piątek', 'sobota', 'niedziela']}


def mail_date(value, lang='es'):
    """Long date in the recipient's language («domingo, 11 de octubre de 2026», «Sunday 11 October 2026»…)."""
    try: d = _dt.date.fromisoformat(str(value)[:10])
    except Exception: return str(value or '')
    if lang == 'es': return es_long_date(d.isoformat())
    if lang == 'en': return f"{_DAYS['en'][d.weekday()]} {d.day} {_MONTHS['en'][d.month - 1]} {d.year}"
    if lang == 'de': return f"{_DAYS['de'][d.weekday()]}, {d.day}. {_MONTHS['de'][d.month - 1]} {d.year}"
    if lang in ('fr', 'it', 'nl'): return f"{_DAYS[lang][d.weekday()]} {d.day} {_MONTHS[lang][d.month - 1]} {d.year}"
    if lang == 'pt': return f"{_DAYS['pt'][d.weekday()]}, {d.day} de {_MONTHS['pt'][d.month - 1]} de {d.year}"
    if lang == 'pl': return f"{_DAYS['pl'][d.weekday()]}, {d.day} {_MONTHS['pl'][d.month - 1]} {d.year} r."
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
    if lang == 'pl':  # 1 234,50 €  (narrow no-break space as thousands separator)
        txt = f'{v:,.2f}'.replace(',', '\u202f').replace('.', ',').removesuffix(',00')
        return f'{txt} {sym}' if sym else f'{txt} {cur}'
    txt = f'{v:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.').removesuffix(',00')
    return f'{txt} {sym}' if sym else f'{txt} {cur}'
