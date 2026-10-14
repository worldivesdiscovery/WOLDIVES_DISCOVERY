"""Service templates managed by the administration (v50.53): «Administración → Plantillas de servicios».

A centre or freelance creates a service from a template: the name, description, duration and photo come from it and
then they set the price and the dates. The card of the service shows the template's photo behind the text (with a veil
that keeps WCAG AA contrast) unless the centre uploads its own photo; changing the template's photo changes it at once
in every service that uses it. Without a template or photo, the neutral photo chosen in «Imágenes de la web».

The titular will send the final list and the photos: these templates start without a photo (the neutral one is used).
"""
from __future__ import annotations

import json
import re

LANGS = ('es', 'en', 'fr', 'de', 'it', 'pt', 'pl', 'nl', 'zh')

SCHEMA = '''CREATE TABLE IF NOT EXISTS service_catalog (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  slug TEXT NOT NULL UNIQUE,
  service_type TEXT NOT NULL DEFAULT 'inmersion',
  names TEXT NOT NULL,
  descriptions TEXT,
  duration_minutes INTEGER,
  max_participants INTEGER,
  booking_mode TEXT NOT NULL DEFAULT 'auto',
  color TEXT,
  photo_base TEXT, photo_widths TEXT, photo_jpg INTEGER, photo_focal TEXT, photo_veil_light REAL, photo_veil_dark REAL,
  photo_credit TEXT, photo_status TEXT, photo_by INTEGER, photo_at TEXT,
  sort_order INTEGER NOT NULL DEFAULT 0,
  active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL, updated_at TEXT NOT NULL, updated_by INTEGER)'''

# slug, type, minutes (orientative), places, booking mode, colour, names (9 languages), descriptions (9 languages)
SEED = [
    ('bautizo', 'experiencia', 150, 4, 'request', '#059669',
     ['Bautizo de buceo', 'Try dive', 'Baptême de plongée', 'Schnuppertauchen', 'Battesimo subacqueo', 'Batismo de mergulho', 'Próbne nurkowanie', 'Proefduik', '体验潜水'],
     ['Primera experiencia bajo el agua con un instructor, sin titulación previa.', 'Your first time under water with an instructor; no certification needed.',
      "Première expérience sous l'eau avec un moniteur, sans brevet.", 'Erstes Erlebnis unter Wasser mit einem Tauchlehrer, ohne Vorkenntnisse.',
      "Prima esperienza sott'acqua con un istruttore, senza brevetto.", 'Primeira experiência debaixo de água com um instrutor, sem certificação.',
      'Pierwsze doświadczenie pod wodą z instruktorem, bez uprawnień.', 'Je eerste ervaring onder water met een instructeur, zonder brevet.', '在教练陪同下的首次水下体验，无需潜水证书。']),
    ('open-water', 'curso', 4320, 4, 'auto', '#d97706',
     ['Curso Open Water', 'Open Water course', 'Cours Open Water', 'Open-Water-Kurs', 'Corso Open Water', 'Curso Open Water', 'Kurs Open Water', 'Open Water-cursus', '开放水域潜水员课程'],
     ['Curso para obtener la primera titulación de buceo: teoría, aguas confinadas e inmersiones en el mar.', 'Course for your first diving certification: theory, confined water and open water dives.',
      'Cours pour obtenir le premier niveau de plongée : théorie, milieu protégé et plongées en mer.', 'Kurs für das erste Tauchbrevet: Theorie, geschütztes Gewässer und Tauchgänge im Meer.',
      'Corso per il primo brevetto subacqueo: teoria, acque confinate e immersioni in mare.', 'Curso para a primeira certificação de mergulho: teoria, águas confinadas e mergulhos no mar.',
      'Kurs na pierwszy stopień nurkowy: teoria, wody osłonięte i nurkowania w morzu.', 'Cursus voor je eerste duikbrevet: theorie, besloten water en duiken in open water.', '获取第一张潜水证书的课程：理论、平静水域训练和开放水域潜水。']),
    ('advanced', 'curso', 2880, 4, 'auto', '#ea580c',
     ['Curso Advanced', 'Advanced course', 'Cours Advanced', 'Advanced-Kurs', 'Corso Advanced', 'Curso Advanced', 'Kurs Advanced', 'Advanced-cursus', '进阶开放水域课程'],
     ['Amplía tu experiencia con inmersiones de aventura: profunda, navegación y otras a elegir.', 'Build experience with adventure dives: deep, navigation and others of your choice.',
      "Élargissez votre expérience avec des plongées d'aventure : profonde, orientation et d'autres au choix.", 'Mehr Erfahrung mit Abenteuertauchgängen: Tieftauchen, Navigation und weitere nach Wahl.',
      "Amplia la tua esperienza con immersioni d'avventura: profonda, navigazione e altre a scelta.", 'Ganha experiência com mergulhos de aventura: profundo, navegação e outros à escolha.',
      'Zdobądź doświadczenie w nurkowaniach przygodowych: głębokim, nawigacyjnym i innych do wyboru.', 'Doe meer ervaring op met avontuurduiken: diep, navigatie en andere naar keuze.', '通过探险潜水积累经验：深潜、导航及其他自选潜水。']),
    ('rescue', 'curso', 4320, 4, 'request', '#dc2626',
     ['Curso Rescue', 'Rescue course', 'Cours Rescue', 'Rescue-Kurs', 'Corso Rescue', 'Curso Rescue', 'Kurs Rescue', 'Rescue-cursus', '救援潜水员课程'],
     ['Aprende a prevenir y resolver problemas bajo el agua y a ayudar a otros buceadores.', 'Learn to prevent and handle problems under water and to help other divers.',
      "Apprenez à prévenir et gérer les problèmes sous l'eau et à aider les autres plongeurs.", 'Lerne, Probleme unter Wasser zu vermeiden und zu lösen und anderen Tauchern zu helfen.',
      "Impara a prevenire e gestire i problemi sott'acqua e ad aiutare altri subacquei.", 'Aprende a prevenir e resolver problemas debaixo de água e a ajudar outros mergulhadores.',
      'Naucz się zapobiegać problemom pod wodą, radzić sobie z nimi i pomagać innym nurkom.', 'Leer problemen onder water voorkomen en oplossen en andere duikers helpen.', '学习预防和处理水下问题，并帮助其他潜水员。']),
    ('divemaster', 'curso', 40320, 2, 'request', '#9a3412',
     ['Curso Divemaster', 'Divemaster course', 'Cours Divemaster', 'Divemaster-Kurs', 'Corso Divemaster', 'Curso Divemaster', 'Kurs Divemaster', 'Divemaster-cursus', '潜水长课程'],
     ['Primer nivel profesional: guía buceadores titulados y ayuda en los cursos.', 'The first professional level: lead certified divers and assist on courses.',
      'Premier niveau professionnel : guider des plongeurs brevetés et assister les cours.', 'Die erste Profistufe: brevetierte Taucher führen und bei Kursen assistieren.',
      'Primo livello professionale: guida subacquei brevettati e assisti nei corsi.', 'Primeiro nível profissional: guia mergulhadores certificados e ajuda nos cursos.',
      'Pierwszy poziom zawodowy: prowadzenie certyfikowanych nurków i asystowanie na kursach.', 'Het eerste professionele niveau: begeleid gebrevetteerde duikers en assisteer bij cursussen.', '第一个专业级别：带领持证潜水员并协助教学。']),
    ('nitrox', 'curso', 240, 6, 'auto', '#ca8a04',
     ['Especialidad Nitrox', 'Nitrox specialty', 'Spécialité Nitrox', 'Nitrox-Spezialkurs', 'Specialità Nitrox', 'Especialidade Nitrox', 'Specjalizacja Nitrox', 'Nitrox-specialisatie', '高氧潜水专长'],
     ['Bucea con aire enriquecido en oxígeno para alargar el tiempo sin descompresión.', 'Dive with oxygen-enriched air for longer no-decompression times.',
      "Plongez à l'air enrichi en oxygène pour allonger le temps sans décompression.", 'Tauche mit sauerstoffangereicherter Luft für längere Nullzeiten.',
      'Immergiti con aria arricchita di ossigeno per allungare il tempo senza decompressione.', 'Mergulha com ar enriquecido em oxigénio para prolongar o tempo sem descompressão.',
      'Nurkuj na powietrzu wzbogaconym w tlen, by wydłużyć czas bez dekompresji.', 'Duik met zuurstofverrijkte lucht voor langere duiktijden zonder decompressie.', '使用高氧空气潜水，延长免减压时间。']),
    ('especialidad', 'curso', 1440, 4, 'request', '#b45309',
     ['Otras especialidades', 'Other specialties', 'Autres spécialités', 'Weitere Spezialkurse', 'Altre specialità', 'Outras especialidades', 'Inne specjalizacje', 'Andere specialisaties', '其他专长课程'],
     ['Cursos para aprender una técnica concreta: fotografía, pecios, flotabilidad y más.', 'Courses to learn a specific skill: photography, wrecks, buoyancy and more.',
      'Cours pour apprendre une technique précise : photo, épaves, flottabilité et plus.', 'Kurse für eine bestimmte Technik: Fotografie, Wracks, Tarierung und mehr.',
      'Corsi per imparare una tecnica precisa: fotografia, relitti, assetto e altro.', 'Cursos para aprender uma técnica concreta: fotografia, naufrágios, flutuabilidade e mais.',
      'Kursy konkretnej umiejętności: fotografia, wraki, pływalność i inne.', 'Cursussen voor een specifieke vaardigheid: fotografie, wrakken, trimmen en meer.', '学习特定技能的课程：水下摄影、沉船、中性浮力等。']),
    ('inmersion-simple', 'inmersion', 120, 12, 'auto', '#0891b2',
     ['Inmersión simple', 'Single dive', 'Plongée simple', 'Einzeltauchgang', 'Immersione singola', 'Mergulho simples', 'Pojedyncze nurkowanie', 'Enkele duik', '单次潜水'],
     ['Una inmersión guiada en uno de los puntos de la zona.', 'One guided dive at one of the local dive sites.',
      "Une plongée guidée sur l'un des sites de la zone.", 'Ein geführter Tauchgang an einem Tauchplatz der Gegend.',
      "Un'immersione guidata in uno dei punti della zona.", 'Um mergulho guiado num dos pontos da zona.',
      'Jedno nurkowanie z przewodnikiem w jednym z miejsc w okolicy.', 'Eén begeleide duik op een van de duikstekken in de buurt.', '在当地潜点进行一次有向导的潜水。']),
    ('inmersion-doble', 'inmersion', 240, 12, 'auto', '#2563eb',
     ['Doble inmersión', 'Double dive', 'Double plongée', 'Doppeltauchgang', 'Doppia immersione', 'Mergulho duplo', 'Podwójne nurkowanie', 'Dubbele duik', '双次潜水'],
     ['Dos inmersiones guiadas en la misma salida, con intervalo en superficie.', 'Two guided dives on the same trip, with a surface interval.',
      'Deux plongées guidées lors de la même sortie, avec intervalle en surface.', 'Zwei geführte Tauchgänge bei derselben Ausfahrt, mit Oberflächenpause.',
      'Due immersioni guidate nella stessa uscita, con intervallo in superficie.', 'Dois mergulhos guiados na mesma saída, com intervalo à superfície.',
      'Dwa nurkowania z przewodnikiem podczas jednego wypadu, z przerwą na powierzchni.', 'Twee begeleide duiken tijdens dezelfde tocht, met een oppervlakte-interval.', '同一趟出海中两次有向导的潜水，中间有水面休息。']),
    ('tercera-inmersion', 'inmersion', 90, 12, 'auto', '#0e7490',
     ['Tercera inmersión', 'Third dive', 'Troisième plongée', 'Dritter Tauchgang', 'Terza immersione', 'Terceiro mergulho', 'Trzecie nurkowanie', 'Derde duik', '第三次潜水'],
     ['Una inmersión más el mismo día, para quien ya ha hecho dos.', 'One more dive on the same day, for those who have already done two.',
      'Une plongée de plus le même jour, pour ceux qui en ont déjà fait deux.', 'Ein weiterer Tauchgang am selben Tag, für alle, die schon zwei gemacht haben.',
      "Un'immersione in più nello stesso giorno, per chi ne ha già fatte due.", 'Mais um mergulho no mesmo dia, para quem já fez dois.',
      'Jeszcze jedno nurkowanie tego samego dnia, dla tych, którzy mają już dwa za sobą.', 'Nog een duik op dezelfde dag, voor wie er al twee heeft gedaan.', '当天的第三次潜水，适合已完成两潜的潜水员。']),
    ('nocturna', 'inmersion', 120, 8, 'auto', '#1e3a8a',
     ['Inmersión nocturna', 'Night dive', 'Plongée de nuit', 'Nachttauchgang', 'Immersione notturna', 'Mergulho noturno', 'Nurkowanie nocne', 'Nachtduik', '夜潜'],
     ['Inmersión al anochecer con linterna, para ver la vida que sale de noche.', 'A dive after dark with a torch, to see the life that comes out at night.',
      'Plongée à la tombée de la nuit avec une lampe, pour voir la vie nocturne.', 'Ein Tauchgang nach Einbruch der Dunkelheit mit Lampe, um das Nachtleben zu sehen.',
      'Immersione al calar della sera con la torcia, per vedere la vita notturna.', 'Mergulho ao anoitecer com lanterna, para ver a vida que sai à noite.',
      'Nurkowanie po zmroku z latarką, by zobaczyć nocne życie.', 'Een duik in het donker met een lamp, om het nachtleven te zien.', '带手电筒的夜间潜水，观察夜间出没的海洋生物。']),
    ('snorkel', 'experiencia', 120, 10, 'auto', '#0d9488',
     ['Snorkel', 'Snorkelling', 'Snorkeling', 'Schnorcheln', 'Snorkeling', 'Snorkeling', 'Snorkeling', 'Snorkelen', '浮潜'],
     ['Excursión en superficie con gafas, tubo y aletas, para todas las edades.', 'A surface outing with mask, snorkel and fins, for all ages.',
      'Sortie en surface avec masque, tuba et palmes, pour tous les âges.', 'Ausflug an der Oberfläche mit Maske, Schnorchel und Flossen, für alle Altersgruppen.',
      'Escursione in superficie con maschera, boccaglio e pinne, per tutte le età.', 'Passeio à superfície com máscara, tubo e barbatanas, para todas as idades.',
      'Wycieczka na powierzchni z maską, fajką i płetwami, dla każdego.', 'Een tocht aan de oppervlakte met masker, snorkel en vinnen, voor alle leeftijden.', '佩戴面镜、呼吸管和脚蹼的水面活动，适合所有年龄。']),
    ('salida-privada', 'salida', 240, 6, 'request', '#6d28d9',
     ['Salida privada', 'Private trip', 'Sortie privée', 'Private Ausfahrt', 'Uscita privata', 'Saída privada', 'Prywatny wypad', 'Privétocht', '私人出海'],
     ['Salida en barco solo para tu grupo, con guía y horario a medida.', 'A boat trip just for your group, with a guide and a schedule to suit you.',
      'Sortie en bateau rien que pour votre groupe, avec guide et horaire sur mesure.', 'Bootsausfahrt nur für deine Gruppe, mit Guide und individuellem Zeitplan.',
      'Uscita in barca solo per il tuo gruppo, con guida e orario su misura.', 'Saída de barco só para o teu grupo, com guia e horário à medida.',
      'Rejs łodzią tylko dla twojej grupy, z przewodnikiem i godzinami na życzenie.', 'Een boottocht alleen voor jouw groep, met gids en een schema op maat.', '专属你团队的出海，配备向导，时间可定制。']),
    ('viaje', 'viaje', 0, 10, 'request', '#7c3aed',
     ['Viaje de buceo', 'Dive trip', 'Voyage plongée', 'Tauchreise', 'Viaggio subacqueo', 'Viagem de mergulho', 'Wyjazd nurkowy', 'Duikreis', '潜水旅行'],
     ['Viaje organizado de varios días con inmersiones, alojamiento y traslados.', 'An organised trip of several days with dives, accommodation and transfers.',
      'Voyage organisé de plusieurs jours avec plongées, hébergement et transferts.', 'Organisierte mehrtägige Reise mit Tauchgängen, Unterkunft und Transfers.',
      'Viaggio organizzato di più giorni con immersioni, alloggio e trasferimenti.', 'Viagem organizada de vários dias com mergulhos, alojamento e transferes.',
      'Zorganizowany kilkudniowy wyjazd z nurkowaniami, noclegiem i transferami.', 'Een georganiseerde meerdaagse reis met duiken, verblijf en transfers.', '包含潜水、住宿和接送的多日组织行程。']),
    ('vida-a-bordo', 'vida_a_bordo', 10080, 12, 'request', '#4338ca',
     ['Vida a bordo', 'Liveaboard', 'Croisière plongée', 'Tauchsafari', 'Crociera subacquea', 'Cruzeiro de mergulho', 'Safari nurkowe', 'Duiksafari', '船宿潜水'],
     ['Varios días a bordo de un barco, con varias inmersiones al día en los mejores puntos.', 'Several days on board a boat, with several dives a day at the best sites.',
      'Plusieurs jours à bord d’un bateau, avec plusieurs plongées par jour sur les meilleurs sites.', 'Mehrere Tage an Bord eines Schiffes, mit mehreren Tauchgängen täglich an den besten Plätzen.',
      'Più giorni a bordo di una barca, con diverse immersioni al giorno nei punti migliori.', 'Vários dias a bordo de um barco, com vários mergulhos por dia nos melhores pontos.',
      'Kilka dni na pokładzie łodzi, z kilkoma nurkowaniami dziennie w najlepszych miejscach.', 'Meerdere dagen aan boord van een schip, met meerdere duiken per dag op de mooiste stekken.', '在船上生活数日，每天在最佳潜点进行多次潜水。']),
    ('alquiler-equipo', 'alquiler_equipo', 0, 0, 'request', '#475569',
     ['Alquiler de equipo', 'Equipment rental', 'Location de matériel', 'Ausrüstungsverleih', 'Noleggio attrezzatura', 'Aluguer de equipamento', 'Wypożyczenie sprzętu', 'Uitrustingsverhuur', '装备租赁'],
     ['Equipo completo o por piezas para tus inmersiones.', 'Full kit or individual items for your dives.',
      'Équipement complet ou à la pièce pour vos plongées.', 'Komplette Ausrüstung oder einzelne Teile für deine Tauchgänge.',
      'Attrezzatura completa o a pezzi per le tue immersioni.', 'Equipamento completo ou por peças para os teus mergulhos.',
      'Pełny zestaw lub pojedyncze elementy sprzętu do nurkowania.', 'Een complete uitrusting of losse onderdelen voor je duiken.', '为你的潜水提供全套或单件装备。']),
]

# Existing services → template (migration and demo): first match on the title wins; nothing matched stays without one.
TITLE_RULES = [
    (r'bautizo|try ?dive|discover scuba', 'bautizo'),
    # The higher course first: «Advanced Open Water» is the Advanced course, «Rescue (requiere Advanced)» the Rescue one.
    (r'divemaster|dive ?master', 'divemaster'),
    (r'rescue|rescate', 'rescue'),
    (r'advanced|avanzado', 'advanced'),
    (r'open ?water', 'open-water'),
    (r'nitrox|eanx', 'nitrox'),
    (r'fotograf|especialidad|specialty|pecio', 'especialidad'),
    (r'snorkel', 'snorkel'),
    (r'nocturn|night', 'nocturna'),
    (r'tercera|third', 'tercera-inmersion'),
    (r'doble|double|dos inmersiones', 'inmersion-doble'),
    (r'privad|private', 'salida-privada'),
    (r'vida a bordo|liveaboard', 'vida-a-bordo'),
    (r'alquiler|rental', 'alquiler-equipo'),
    (r'inmersi[oó]n|buceo simple|single dive|atardecer|cenote', 'inmersion-simple'),
]
TYPE_DEFAULT = {'viaje': 'viaje', 'vida_a_bordo': 'vida-a-bordo', 'alquiler_equipo': 'alquiler-equipo'}


def guess_slug(title: str, service_type: str | None = None) -> str | None:
    t = (title or '').lower()
    for rx, slug in TITLE_RULES:
        if re.search(rx, t): return slug
    return TYPE_DEFAULT.get(service_type or '')


def seed(db, now: str):
    for i, (slug, stype, minutes, places, mode, color, names, descs) in enumerate(SEED):
        db.execute('''INSERT OR IGNORE INTO service_catalog(slug,service_type,names,descriptions,duration_minutes,max_participants,booking_mode,color,
                      sort_order,active,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,1,?,?)''',
                   (slug, stype, json.dumps(dict(zip(LANGS, names)), ensure_ascii=False), json.dumps(dict(zip(LANGS, descs)), ensure_ascii=False),
                    minutes or None, places or None, mode, color, (i + 1) * 10, now, now))


def text_in(value: str | None, lang: str) -> tuple[str, bool]:
    """(text, pending): the text in `lang`; in Spanish when that language has none yet («Pendiente de traducción»)."""
    try: d = json.loads(value or '{}')
    except (TypeError, ValueError): d = {}
    if d.get(lang): return d[lang], False
    return d.get('es') or next(iter(d.values()), ''), lang != 'es'


def clean_texts(raw, limit: int) -> dict:
    """{lang: text} from the admin form: only the 9 languages, trimmed; Spanish is required."""
    out = {}
    if isinstance(raw, dict):
        for lang in LANGS:
            v = re.sub(r'\s+', ' ', str(raw.get(lang) or '')).strip()[:limit]
            if v: out[lang] = v
    return out


FOCAL_RX = re.compile(r'^(\d{1,3}(?:\.\d+)?),(\d{1,3}(?:\.\d+)?)$')


def clean_focal(value) -> str:
    """Focal point «x,y» in % of the photo (where the crop centres), 50,50 by default."""
    m = FOCAL_RX.match(str(value or '').strip())
    if not m: return '50,50'
    x, y = (min(100.0, max(0.0, float(v))) for v in m.groups())
    return f'{round(x, 1):g},{round(y, 1):g}'


def photo_payload(url_base: str | None, widths, jpg, focal, veil_light, veil_dark, *, own: bool = False, source: str = '') -> dict | None:
    """What a card needs to draw the photo: WebP srcset, JPG for older browsers, focal point and minimum veils."""
    if not url_base: return None
    ws = [int(x) for x in str(widths or '').split(',') if str(x).strip().isdigit()]
    out = {'srcset': ', '.join(f'{url_base}-{w}.webp {w}w' for w in ws), 'src': f'{url_base}-{ws[min(1, len(ws) - 1)]}.webp' if ws else None,
           'jpg': f'{url_base}-{jpg}.jpg' if jpg else None, 'focal': clean_focal(focal),
           'veil': {'light': float(veil_light or 0), 'dark': float(veil_dark or 0)}, 'own': own, 'source': source}
    if not out['src'] and not out['jpg']: return None
    return out
