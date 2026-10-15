"""v50.55 · Texts of the app's «Para terminar» (brief completo de la app): the point page in the 9 languages of the web
and the app's screens in es, en and fr.
    python3 scripts/idiomas/datos/v50_55_terminar.py
then: python3 scripts/idiomas/web_textos.py scripts/idiomas/datos/web_v50_55_terminar.json
      python3 scripts/idiomas/app_textos.py scripts/idiomas/datos/app_v50_55_terminar.json
Order of each web list: en, fr, de, it, pt, pl, nl, zh (the app lists: en, fr)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LANGS = ['en', 'fr', 'de', 'it', 'pt', 'pl', 'nl', 'zh']

WEB = {
 'Próximas salidas aquí': ['Next departures here', 'Prochaines sorties ici', 'Nächste Ausfahrten hier', 'Prossime uscite qui', 'Próximas saídas aqui', 'Najbliższe wypłynięcia tutaj', 'Volgende vertrekken hier', '此处的近期出海'],
 'Ver salidas aquí': ['See departures here', 'Voir les sorties ici', 'Ausfahrten hier ansehen', 'Vedi le uscite qui', 'Ver saídas aqui', 'Zobacz wypłynięcia tutaj', 'Vertrekken hier bekijken', '查看此处的出海'],
 'plaza': ['place', 'place', 'Platz', 'posto', 'lugar', 'miejsce', 'plaats', '个名额'],
 # the booking page of a freelance (and of «Pago en persona»)
 'PROFESIONAL': ['PROFESSIONAL', 'PROFESSIONNEL', 'PROFI', 'PROFESSIONISTA', 'PROFISSIONAL', 'PROFESJONALISTA', 'PROFESSIONAL', '专业人员'],
 'Punto a concretar con el profesional': ['Dive site to be agreed with the professional', 'Site à convenir avec le professionnel', 'Tauchplatz nach Absprache mit dem Profi', 'Punto da concordare con il professionista', 'Ponto a combinar com o profissional', 'Miejsce do uzgodnienia z profesjonalistą', 'Duikstek af te spreken met de professional', '潜点待与专业人员商定'],
 'A concretar con el profesional': ['To be agreed with the professional', 'À convenir avec le professionnel', 'Nach Absprache mit dem Profi', 'Da concordare con il professionista', 'A combinar com o profissional', 'Do uzgodnienia z profesjonalistą', 'Af te spreken met de professional', '待与专业人员商定'],
 'La reserva está confirmada. Acuerda con el profesional la forma de pago y los detalles por WhatsApp.':
  ['Your booking is confirmed. Agree the way of paying and the details with the professional on WhatsApp.',
   'La réservation est confirmée. Convenez avec le professionnel du mode de paiement et des détails par WhatsApp.',
   'Die Buchung ist bestätigt. Vereinbare die Zahlungsweise und die Details per WhatsApp mit dem Profi.',
   'La prenotazione è confermata. Concorda con il professionista il modo di pagamento e i dettagli su WhatsApp.',
   'A reserva está confirmada. Combina com o profissional a forma de pagamento e os detalhes por WhatsApp.',
   'Rezerwacja jest potwierdzona. Uzgodnij z profesjonalistą formę płatności i szczegóły przez WhatsApp.',
   'De boeking is bevestigd. Spreek de manier van betalen en de details af met de professional via WhatsApp.',
   '预订已确认。请通过 WhatsApp 与专业人员商定付款方式和细节。'],
}
APP = {
 'Pagar': ['Pay', 'Payer'],
 'Calendario': ['Calendar', 'Calendrier'],
 'Repetir reserva': ['Book again', 'Réserver à nouveau'],
 'El plazo para pagar ha terminado.': ['The time to pay has ended.', 'Le délai pour payer est terminé.'],
 'Tiempo para pagar': ['Time left to pay', 'Temps restant pour payer'],
 'Falta contar a la vuelta': ['Count on the way back', 'Comptage au retour à faire'],
 'Contados a la vuelta': ['Counted on the way back', 'Comptés au retour'],
 'Al salir contaste': ['When leaving you counted', 'Au départ, vous avez compté'],
 'Antes de terminar la salida, cuenta otra vez a todos en el barco.': ['Before the departure ends, count everyone on the boat again.', 'Avant la fin de la sortie, recomptez tout le monde sur le bateau.'],
 'Contar a la vuelta': ['Count on the way back', 'Compter au retour'],
}


def main():
    for k, v in WEB.items(): assert len(v) == 8, k
    for k, v in APP.items(): assert len(v) == 2, k
    datos = ROOT / 'scripts' / 'idiomas' / 'datos'
    (datos / 'web_v50_55_terminar.json').write_text(json.dumps({'exact': {es: dict(zip(LANGS, v)) for es, v in WEB.items()}, 'patterns': {}}, ensure_ascii=False, indent=1), encoding='utf-8')
    (datos / 'app_v50_55_terminar.json').write_text(json.dumps(APP, ensure_ascii=False, indent=1), encoding='utf-8')
    print('ok', len(WEB), 'web,', len(APP), 'app')


if __name__ == '__main__':
    sys.exit(main())
