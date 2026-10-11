"""Own descriptions of the dive points (v50.36, Fase 5.9).

The catalogue texts are written from the factual data of each point (place, type of dive, depths, level and access),
never copied from a third party. When a point has extra facts checked by WORLDIVES («what you see» and a practical
tip), they are added. Missing data are not invented: they are listed in `missing` so the owner or a centre can fill
them in from Administración.

Structure (the same in the 10 languages):
  1. Summary: where it is, type of dive, depth and recommended level.
  2. What you see (only when there are checked facts).
  3. Access and tips, ending with the reminder to check the conditions of the day with the centre.
"""

LANGS = ('es', 'en', 'fr', 'de', 'it', 'pt', 'nl', 'pl', 'ru', 'zh')

# Type of dive (catalogue values in Spanish) → canonical key.
TYPE_KEYS = {
    'pared': 'wall', 'arrecife': 'reef', 'arrecifes': 'reef', 'fondo arenoso': 'sand', 'túnel': 'tunnel', 'tunel': 'tunnel',
    'cueva': 'cave', 'cuevas': 'cave', 'caverna': 'cavern', 'cañón': 'canyon', 'canon': 'canyon', 'cenote': 'cenote', 'canal': 'channel',
    'corrientes': 'current', 'deriva': 'drift', 'lago': 'lake', 'muck': 'muck', 'pecio': 'wreck', 'pico': 'pinnacle', 'pilar': 'pinnacle',
    'pinnacle': 'pinnacle', 'pináculo': 'pinnacle', 'pinaculo': 'pinnacle', 'aguas profundas': 'blue',
}
TYPES = {
    'wall': ('pared', 'wall', 'tombant', 'Steilwand', 'parete', 'parede', 'wand', 'ściana', 'стена', '岩壁'),
    'reef': ('arrecife', 'reef', 'récif', 'Riff', 'reef', 'recife', 'rif', 'rafa', 'риф', '礁石'),
    'sand': ('fondo arenoso', 'sandy bottom', 'fond sableux', 'Sandgrund', 'fondale sabbioso', 'fundo de areia', 'zandbodem', 'piaszczyste dno', 'песчаное дно', '沙底'),
    'tunnel': ('túnel', 'tunnel', 'tunnel', 'Tunnel', 'tunnel', 'túnel', 'tunnel', 'tunel', 'тоннель', '隧道'),
    'cave': ('cueva', 'cave', 'grotte', 'Höhle', 'grotta', 'gruta', 'grot', 'jaskinia', 'пещера', '洞穴'),
    'cavern': ('caverna', 'cavern', 'caverne', 'Kaverne', 'caverna', 'caverna', 'caverne', 'kawerna', 'грот', '洞窟'),
    'canyon': ('cañón', 'canyon', 'canyon', 'Canyon', 'canyon', 'cânion', 'canyon', 'kanion', 'каньон', '峡谷'),
    'cenote': ('cenote', 'cenote', 'cénote', 'Cenote', 'cenote', 'cenote', 'cenote', 'cenota', 'сенот', '天然井'),
    'channel': ('canal', 'channel', 'chenal', 'Kanal', 'canale', 'canal', 'kanaal', 'kanał', 'канал', '水道'),
    'current': ('corrientes', 'currents', 'courants', 'Strömung', 'correnti', 'correntes', 'stroming', 'prądy', 'течения', '洋流'),
    'drift': ('deriva', 'drift', 'dérive', 'Strömungstauchgang', 'deriva', 'deriva', 'driftduik', 'dryf', 'дрифт', '放流潜'),
    'lake': ('lago', 'lake', 'lac', 'See', 'lago', 'lago', 'meer', 'jezioro', 'озеро', '湖泊'),
    'muck': ('muck', 'muck', 'muck', 'Muck', 'muck', 'muck', 'muck', 'muck', 'мак-дайвинг', '泥底潜'),
    'wreck': ('pecio', 'wreck', 'épave', 'Wrack', 'relitto', 'naufrágio', 'wrak', 'wrak', 'затонувшее судно', '沉船'),
    'pinnacle': ('pináculo', 'pinnacle', 'pinacle', 'Felsnadel', 'pinnacolo', 'pináculo', 'pinakel', 'iglica', 'скальный пик', '尖礁'),
    'blue': ('aguas profundas', 'blue water', 'pleine eau', 'Freiwasser', 'acque profonde', 'águas profundas', 'diep water', 'głęboka woda', 'открытая вода', '深水'),
}
LEVEL_KEYS = {'fácil': 'easy', 'facil': 'easy', 'iniciación': 'easy', 'iniciacion': 'easy', 'principiante': 'easy',
              'moderado': 'mid', 'intermedio': 'mid', 'intermedia': 'mid', 'avanzado': 'adv'}
LEVELS = {
    'easy': ('iniciación', 'beginner', 'débutant', 'Einsteiger', 'principiante', 'iniciante', 'beginner', 'początkujący', 'начальный', '入门'),
    'mid': ('intermedio', 'intermediate', 'intermédiaire', 'mittel', 'intermedio', 'intermediário', 'gemiddeld', 'średniozaawansowany', 'средний', '中级'),
    'adv': ('avanzado', 'advanced', 'confirmé', 'erfahren', 'avanzato', 'avançado', 'gevorderd', 'zaawansowany', 'продвинутый', '高级'),
}
T = {
    'place': ('Inmersión en {place}.', 'A dive in {place}.', 'Plongée à {place}.', 'Tauchplatz in {place}.', 'Immersione a {place}.',
              'Mergulho em {place}.', 'Duikstek in {place}.', 'Nurkowisko w miejscu {place}.', 'Место погружения: {place}.', '潜点位于{place}。'),
    'types': ('Tipo de inmersión: {types}.', 'Type of dive: {types}.', 'Type de plongée : {types}.', 'Art des Tauchgangs: {types}.', 'Tipo di immersione: {types}.',
              'Tipo de mergulho: {types}.', 'Soort duik: {types}.', 'Rodzaj nurkowania: {types}.', 'Тип погружения: {types}.', '潜水类型：{types}。'),
    'depth': ('Profundidad de {min} a {max} m.', 'Depth from {min} to {max} m.', 'Profondeur de {min} à {max} m.', 'Tiefe von {min} bis {max} m.', 'Profondità da {min} a {max} m.',
              'Profundidade de {min} a {max} m.', 'Diepte van {min} tot {max} m.', 'Głębokość od {min} do {max} m.', 'Глубина от {min} до {max} м.', '深度{min}至{max}米。'),
    'depth_max': ('Profundidad máxima: {max} m.', 'Maximum depth: {max} m.', 'Profondeur maximale : {max} m.', 'Maximale Tiefe: {max} m.', 'Profondità massima: {max} m.',
                  'Profundidade máxima: {max} m.', 'Maximale diepte: {max} m.', 'Maksymalna głębokość: {max} m.', 'Максимальная глубина: {max} м.', '最大深度：{max}米。'),
    'level': ('Nivel recomendado: {level}.', 'Recommended level: {level}.', 'Niveau conseillé : {level}.', 'Empfohlenes Niveau: {level}.', 'Livello consigliato: {level}.',
              'Nível recomendado: {level}.', 'Aanbevolen niveau: {level}.', 'Zalecany poziom: {level}.', 'Рекомендуемый уровень: {level}.', '建议水平：{level}。'),
    'boat': ('Se accede en barco.', 'Access by boat.', 'Accès en bateau.', 'Zugang per Boot.', 'Si raggiunge in barca.', 'Acesso de barco.', 'Bereikbaar per boot.',
             'Dostęp łodzią.', 'Доступ на лодке.', '乘船前往。'),
    'boat_from': ('Se accede en barco desde {from_}.', 'Access by boat from {from_}.', 'Accès en bateau depuis {from_}.', 'Zugang per Boot ab {from_}.', 'Si raggiunge in barca da {from_}.',
                  'Acesso de barco a partir de {from_}.', 'Bereikbaar per boot vanuit {from_}.', 'Dostęp łodzią z {from_}.', 'Доступ на лодке из {from_}.', '从{from_}乘船前往。'),
    'shore': ('Se accede desde la orilla.', 'Access from the shore.', 'Accès depuis le bord.', 'Zugang vom Ufer.', 'Si accede da riva.', 'Acesso pela costa.', 'Bereikbaar vanaf de kant.',
              'Wejście z brzegu.', 'Вход с берега.', '从岸边下水。'),
    'boat_shore': ('Se accede en barco o desde la orilla.', 'Access by boat or from the shore.', 'Accès en bateau ou depuis le bord.', 'Zugang per Boot oder vom Ufer.',
                   'Si raggiunge in barca o da riva.', 'Acesso de barco ou pela costa.', 'Bereikbaar per boot of vanaf de kant.', 'Dostęp łodzią lub z brzegu.',
                   'Доступ на лодке или с берега.', '可乘船或从岸边下水。'),
    'regulated': ('El acceso está regulado en parte de la zona.', 'Access is regulated in part of the area.', "L'accès est réglementé sur une partie de la zone.",
                  'Der Zugang ist in Teilen des Gebiets geregelt.', "L'accesso è regolamentato in parte della zona.", 'O acesso é regulado em parte da zona.',
                  'De toegang is in een deel van het gebied gereguleerd.', 'Dostęp do części obszaru jest regulowany.', 'Доступ в часть зоны ограничен.', '部分区域限制进入。'),
    'check': ('Confirma con el centro las condiciones del día antes de bucear.', 'Check the conditions of the day with the dive centre before diving.',
              'Vérifiez les conditions du jour avec le centre avant de plonger.', 'Kläre die Bedingungen des Tages vor dem Tauchgang mit der Basis.',
              'Verifica con il centro le condizioni del giorno prima di immergerti.', 'Confirme com o centro as condições do dia antes de mergulhar.',
              'Vraag het duikcentrum naar de omstandigheden van de dag voordat je duikt.', 'Przed nurkowaniem sprawdź z centrum warunki danego dnia.',
              'Перед погружением уточните в центре условия дня.', '下水前请向潜水中心确认当天的条件。'),
}
_AND = ('y', 'and', 'et', 'und', 'e', 'e', 'en', 'i', 'и', '和')


def _num(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if f <= 0: return None
    return int(f) if f == int(f) else round(f, 1)


def _list(items, lang):
    i = LANGS.index(lang)
    if lang == 'zh': return '、'.join(items)
    if len(items) < 2: return ''.join(items)
    return ', '.join(items[:-1]) + f' {_AND[i]} ' + items[-1]


def type_keys(dive_type):
    out = []
    for part in str(dive_type or '').replace('/', '·').split('·'):
        k = TYPE_KEYS.get(part.strip().lower())
        if k and k not in out: out.append(k)
    return out


def access_kind(access):
    """(kind, from, regulated) from the catalogue text; kind is None when the access is unknown."""
    a = str(access or '').strip()
    low = a.lower()
    if not a or 'pendiente' in low: return None, '', False
    regulated = 'regulad' in low
    head = a.split(';')[0].strip()
    hl = head.lower()
    if 'barco' in hl and 'orilla' in hl: return 'boat_shore', '', regulated
    if hl.startswith('barco desde '): return 'boat_from', head[len('barco desde '):].replace(' o ', ' / '), regulated
    if hl.startswith('barco'): return 'boat', '', regulated
    if hl.startswith('orilla'): return 'shore', '', regulated
    return 'other', head, regulated


def describe(p, lang='es', exact=None, extra=None):
    """Text of a point in `lang` and the list of data still missing (in Spanish, for the administration).
    p: row with name, country, region, dive_type, min_depth, max_depth, difficulty, access_info.
    exact: the language pack (Spanish → language) used for country and region names.
    extra: {'see': {lang: text}, 'tips': {lang: text}} with checked facts."""
    lang = lang if lang in LANGS else 'es'
    i = LANGS.index(lang); exact = exact or {}
    tr = lambda s: exact.get(s, s) if lang != 'es' and s else s
    region, country = (p.get('region') or '').strip(), (p.get('country') or '').strip()
    place = ('，' if lang == 'zh' else ', ').join(x for x in (tr(region), tr(country)) if x)
    sp = '' if lang == 'zh' else ' '
    missing = []
    s1 = []
    if place: s1.append(T['place'][i].format(place=place))
    tk = type_keys(p.get('dive_type'))
    if tk: s1.append(T['types'][i].format(types=_list([TYPES[k][i] for k in tk], lang)))
    else: missing.append('tipo de inmersión')
    mn, mx = _num(p.get('min_depth')), _num(p.get('max_depth'))
    if mn is not None and mx is not None and mx > mn: s1.append(T['depth'][i].format(min=mn, max=mx))
    elif mx is not None: s1.append(T['depth_max'][i].format(max=mx))
    else: missing.append('profundidad')
    lk = LEVEL_KEYS.get(str(p.get('difficulty') or '').strip().lower())
    if lk: s1.append(T['level'][i].format(level=LEVELS[lk][i]))
    else: missing.append('nivel recomendado')
    paras = [sp.join(s1)]
    sees = (extra or {}).get('see') or {}
    see = sees.get(lang) or sees.get('en') or ''
    if see: paras.append(see.strip())
    else: missing.append('qué se ve (fondo y vida marina)')
    s3 = []
    kind, frm, regulated = access_kind(p.get('access_info'))
    if kind in ('boat', 'shore', 'boat_shore'): s3.append(T[kind][i])
    elif kind == 'boat_from': s3.append(T['boat_from'][i].format(from_=frm))
    elif kind == 'other':
        if lang == 'es': s3.append(frm.rstrip('.') + '.')
    else: missing.append('acceso')
    if regulated: s3.append(T['regulated'][i])
    tip = ((extra or {}).get('tips') or {}).get(lang) or ''
    if tip: s3.append(tip.strip())
    s3.append(T['check'][i])
    paras.append(sp.join(s3))
    return '\n\n'.join(x for x in paras if x), missing
