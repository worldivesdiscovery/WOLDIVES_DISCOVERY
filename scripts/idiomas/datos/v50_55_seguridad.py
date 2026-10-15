"""v50.55 · Texts of «Seguridad de la app WORLDIVES PRO» (encargo 2): the web in 9 languages, the new-device e-mail and
the app's lock screens (the app speaks es, en and fr).
    python3 scripts/idiomas/datos/v50_55_seguridad.py   → writes web_v50_55_seguridad.json, app_v50_55_seguridad.json
                                                          and adds the e-mail texts to app/emails/<lang>.json
then: python3 scripts/idiomas/web_textos.py scripts/idiomas/datos/web_v50_55_seguridad.json
      python3 scripts/idiomas/app_textos.py scripts/idiomas/datos/app_v50_55_seguridad.json
Order of each list: en, fr, de, it, pt, pl, nl, zh (the app lists: en, fr)."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LANGS = ['en', 'fr', 'de', 'it', 'pt', 'pl', 'nl', 'zh']

# «Dispositivos conectados» (web and app), the team's sessions and the server's answers shown in the web.
WEB = {
 'Dispositivos conectados': ['Connected devices', 'Appareils connectés', 'Verbundene Geräte', 'Dispositivi connessi', 'Dispositivos ligados', 'Połączone urządzenia', 'Verbonden apparaten', '已连接的设备'],
 'Dónde está abierta tu cuenta ahora: navegadores y la app. Si ves algo que no reconoces, cierra ese dispositivo y cambia tu contraseña.':
  ['Where your account is open now: browsers and the app. If you see something you do not recognise, sign that device out and change your password.',
   "Où votre compte est ouvert en ce moment : navigateurs et application. Si vous voyez quelque chose que vous ne reconnaissez pas, déconnectez cet appareil et changez votre mot de passe.",
   'Wo dein Konto gerade geöffnet ist: Browser und App. Wenn du etwas nicht erkennst, melde dieses Gerät ab und ändere dein Passwort.',
   "Dove è aperto ora il tuo account: browser e app. Se vedi qualcosa che non riconosci, disconnetti quel dispositivo e cambia la password.",
   'Onde a tua conta está aberta agora: navegadores e a app. Se vires algo que não reconheces, termina a sessão nesse dispositivo e muda a tua palavra-passe.',
   'Gdzie Twoje konto jest teraz otwarte: przeglądarki i aplikacja. Jeśli widzisz coś, czego nie rozpoznajesz, wyloguj to urządzenie i zmień hasło.',
   'Waar je account nu open is: browsers en de app. Zie je iets wat je niet herkent, meld dat apparaat dan af en wijzig je wachtwoord.',
   '你的账户当前在哪些地方登录：浏览器和应用。如果看到不认识的设备，请将其退出登录并修改密码。'],
 'Cerrar todas menos esta': ['Sign out everywhere else', 'Fermer toutes sauf celle-ci', 'Alle außer dieser abmelden', 'Chiudi tutte tranne questa', 'Fechar todas menos esta', 'Zamknij wszystkie oprócz tej', 'Alle behalve deze afmelden', '退出除此之外的所有会话'],
 'Este dispositivo': ['This device', 'Cet appareil', 'Dieses Gerät', 'Questo dispositivo', 'Este dispositivo', 'To urządzenie', 'Dit apparaat', '此设备'],
 'Última actividad': ['Last activity', 'Dernière activité', 'Letzte Aktivität', 'Ultima attività', 'Última atividade', 'Ostatnia aktywność', 'Laatste activiteit', '最近活动'],
 'Ciudad aproximada': ['Approximate city', 'Ville approximative', 'Ungefähre Stadt', 'Città approssimativa', 'Cidade aproximada', 'Przybliżone miasto', 'Geschatte stad', '大致城市'],
 'Pide la contraseña de nuevo el': ['Asks for the password again on', 'Redemande le mot de passe le', 'Fragt erneut nach dem Passwort am', 'Chiede di nuovo la password il', 'Pede a palavra-passe de novo a', 'Ponownie poprosi o hasło', 'Vraagt opnieuw om het wachtwoord op', '再次要求输入密码的日期：'],
 'La ciudad aproximada aparecerá cuando el servidor la reciba de su proxy (pendiente de configurar).':
  ['The approximate city will appear when the server receives it from its proxy (still to be configured).',
   "La ville approximative apparaîtra lorsque le serveur la recevra de son proxy (à configurer).",
   'Die ungefähre Stadt erscheint, sobald der Server sie von seinem Proxy erhält (noch einzurichten).',
   'La città approssimativa comparirà quando il server la riceverà dal suo proxy (da configurare).',
   'A cidade aproximada aparecerá quando o servidor a receber do seu proxy (por configurar).',
   'Przybliżone miasto pojawi się, gdy serwer otrzyma je od swojego proxy (do skonfigurowania).',
   'De geschatte stad verschijnt zodra de server die van zijn proxy ontvangt (nog in te stellen).',
   '服务器从其代理收到大致城市后会显示（待配置）。'],
 'Cerrar la sesión de ese dispositivo': ['Sign out that device', 'Déconnecter cet appareil', 'Dieses Gerät abmelden', 'Disconnetti quel dispositivo', 'Terminar a sessão nesse dispositivo', 'Wyloguj to urządzenie', 'Dat apparaat afmelden', '退出该设备的登录'],
 'Tendrá que volver a entrar con la contraseña. Si es un móvil, borrará sus datos guardados al conectarse.':
  ['It will have to sign in again with the password. If it is a phone, it will delete its saved data when it connects.',
   "Il faudra se reconnecter avec le mot de passe. Si c'est un téléphone, il effacera ses données enregistrées à la prochaine connexion.",
   'Dort muss man sich erneut mit dem Passwort anmelden. Ist es ein Handy, löscht es beim Verbinden seine gespeicherten Daten.',
   'Dovrà accedere di nuovo con la password. Se è un telefono, cancellerà i dati salvati quando si connette.',
   'Terá de voltar a entrar com a palavra-passe. Se for um telemóvel, apagará os dados guardados ao ligar-se.',
   'Trzeba będzie zalogować się ponownie hasłem. Jeśli to telefon, po połączeniu usunie zapisane dane.',
   'Er moet opnieuw met het wachtwoord worden aangemeld. Is het een telefoon, dan wist die zijn opgeslagen gegevens zodra hij verbinding maakt.',
   '需要重新用密码登录。如果是手机，联网时会删除其保存的数据。'],
 'Sesión cerrada en ese dispositivo.': ['Signed out on that device.', 'Session fermée sur cet appareil.', 'Auf diesem Gerät abgemeldet.', 'Sessione chiusa su quel dispositivo.', 'Sessão terminada nesse dispositivo.', 'Wylogowano na tym urządzeniu.', 'Afgemeld op dat apparaat.', '已在该设备上退出登录。'],
 'Sesiones': ['Sessions', 'Sessions', 'Sitzungen', 'Sessioni', 'Sessões', 'Sesje', 'Sessies', '会话'],
 'Sesiones de': ['Sessions of', 'Sessions de', 'Sitzungen von', 'Sessioni di', 'Sessões de', 'Sesje:', 'Sessies van', '会话：'],
 'No tiene ninguna sesión abierta.': ['They have no open session.', "Cette personne n'a aucune session ouverte.", 'Keine offene Sitzung.', 'Non ha nessuna sessione aperta.', 'Não tem nenhuma sessão aberta.', 'Nie ma żadnej otwartej sesji.', 'Heeft geen open sessie.', '没有任何已打开的会话。'],
 'Al cerrarlas tendrá que volver a entrar con su contraseña; en el móvil se borran los datos guardados.':
  ['Once they are closed, this person will have to sign in again with their password; the phone deletes its saved data.',
   "Une fois fermées, cette personne devra se reconnecter avec son mot de passe ; le téléphone efface ses données enregistrées.",
   'Danach muss sich die Person erneut mit ihrem Passwort anmelden; auf dem Handy werden die gespeicherten Daten gelöscht.',
   'Dopo averle chiuse dovrà accedere di nuovo con la sua password; sul telefono si cancellano i dati salvati.',
   'Ao fechá-las, terá de voltar a entrar com a sua palavra-passe; no telemóvel apagam-se os dados guardados.',
   'Po ich zamknięciu ta osoba będzie musiała zalogować się ponownie hasłem; telefon usunie zapisane dane.',
   'Daarna moet deze persoon opnieuw met het eigen wachtwoord aanmelden; op de telefoon worden de opgeslagen gegevens gewist.',
   '关闭后，此人需要用自己的密码重新登录；手机上保存的数据会被删除。'],
 'Cerrar todas sus sesiones': ['Close all their sessions', 'Fermer toutes ses sessions', 'Alle Sitzungen beenden', 'Chiudi tutte le sue sessioni', 'Fechar todas as sessões', 'Zamknij wszystkie sesje tej osoby', 'Al zijn of haar sessies sluiten', '关闭其所有会话'],
 'Sesiones cerradas': ['Sessions closed', 'Sessions fermées', 'Sitzungen beendet', 'Sessioni chiuse', 'Sessões fechadas', 'Zamknięte sesje', 'Sessies gesloten', '已关闭的会话'],
 # answers of the server shown in the web
 'Es este dispositivo: usa «Cerrar sesión».': ['It is this device: use "Sign out".', "C'est cet appareil : utilisez « Se déconnecter ».", 'Das ist dieses Gerät: Nutze „Abmelden“.', 'È questo dispositivo: usa «Esci».', 'É este dispositivo: usa «Terminar sessão».', 'To jest to urządzenie: użyj „Wyloguj”.', 'Dit is dit apparaat: gebruik "Afmelden".', '这是当前设备：请使用「退出登录」。'],
 'Ese dispositivo ya no tiene la sesión abierta.': ['That device is no longer signed in.', "Cet appareil n'a plus de session ouverte.", 'Dieses Gerät ist nicht mehr angemeldet.', 'Quel dispositivo non ha più la sessione aperta.', 'Esse dispositivo já não tem a sessão aberta.', 'To urządzenie nie jest już zalogowane.', 'Dat apparaat is niet meer aangemeld.', '该设备已不再登录。'],
 'Para tus propias sesiones usa «Dispositivos conectados».': ['For your own sessions use "Connected devices".', 'Pour vos propres sessions, utilisez « Appareils connectés ».', 'Für deine eigenen Sitzungen nutze „Verbundene Geräte“.', 'Per le tue sessioni usa «Dispositivi connessi».', 'Para as tuas próprias sessões usa «Dispositivos ligados».', 'Do własnych sesji użyj „Połączone urządzenia”.', 'Gebruik voor je eigen sessies "Verbonden apparaten".', '管理你自己的会话请使用「已连接的设备」。'],
 'Esa persona no es del equipo.': ['That person is not in the team.', "Cette personne ne fait pas partie de l'équipe.", 'Diese Person gehört nicht zum Team.', 'Quella persona non fa parte del team.', 'Essa pessoa não é da equipa.', 'Ta osoba nie należy do zespołu.', 'Die persoon hoort niet bij het team.', '此人不属于团队。'],
 'No puedes cerrar las sesiones de otro propietario.': ['You cannot close the sessions of another owner.', "Vous ne pouvez pas fermer les sessions d'un autre propriétaire.", 'Du kannst die Sitzungen eines anderen Inhabers nicht beenden.', 'Non puoi chiudere le sessioni di un altro titolare.', 'Não podes fechar as sessões de outro proprietário.', 'Nie możesz zamknąć sesji innego właściciela.', 'Je kunt de sessies van een andere eigenaar niet sluiten.', '你不能关闭其他所有者的会话。'],
 'Tu sesión en este móvil ha terminado. Vuelve a entrar.': ['Your session on this phone has ended. Sign in again.', 'Votre session sur ce téléphone est terminée. Reconnectez-vous.', 'Deine Sitzung auf diesem Handy ist beendet. Melde dich erneut an.', 'La tua sessione su questo telefono è terminata. Accedi di nuovo.', 'A tua sessão neste telemóvel terminou. Volta a entrar.', 'Twoja sesja na tym telefonie się zakończyła. Zaloguj się ponownie.', 'Je sessie op deze telefoon is beëindigd. Meld je opnieuw aan.', '你在此手机上的会话已结束。请重新登录。'],
 'Tu sesión en este móvil ha terminado.': ['Your session on this phone has ended.', 'Votre session sur ce téléphone est terminée.', 'Deine Sitzung auf diesem Handy ist beendet.', 'La tua sessione su questo telefono è terminata.', 'A tua sessão neste telemóvel terminou.', 'Twoja sesja na tym telefonie się zakończyła.', 'Je sessie op deze telefoon is beëindigd.', '你在此手机上的会话已结束。'],
}

# The e-mail «Nuevo inicio de sesión» (new_device_login).
EMAIL = {
 'Nuevo inicio de sesión en tu cuenta de WORLDIVES': ['New sign-in to your WORLDIVES account', 'Nouvelle connexion à votre compte WORLDIVES', 'Neue Anmeldung bei deinem WORLDIVES-Konto', 'Nuovo accesso al tuo account WORLDIVES', 'Novo início de sessão na tua conta WORLDIVES', 'Nowe logowanie na Twoje konto WORLDIVES', 'Nieuwe aanmelding op je WORLDIVES-account', '你的 WORLDIVES 账户有新的登录'],
 'Nuevo inicio de sesión': ['New sign-in', 'Nouvelle connexion', 'Neue Anmeldung', 'Nuovo accesso', 'Novo início de sessão', 'Nowe logowanie', 'Nieuwe aanmelding', '新的登录'],
 'Hola {first_name}, alguien ha entrado en tu cuenta de WORLDIVES desde un dispositivo que no habíamos visto: {device}, el {when}.':
  ['Hello {first_name}, someone signed in to your WORLDIVES account from a device we had not seen before: {device}, on {when}.',
   "Bonjour {first_name}, quelqu'un s'est connecté à votre compte WORLDIVES depuis un appareil que nous n'avions jamais vu : {device}, le {when}.",
   'Hallo {first_name}, jemand hat sich von einem Gerät, das wir noch nicht kannten, bei deinem WORLDIVES-Konto angemeldet: {device}, am {when}.',
   'Ciao {first_name}, qualcuno è entrato nel tuo account WORLDIVES da un dispositivo che non avevamo mai visto: {device}, il {when}.',
   'Olá {first_name}, alguém entrou na tua conta WORLDIVES a partir de um dispositivo que não conhecíamos: {device}, a {when}.',
   'Cześć {first_name}, ktoś zalogował się na Twoje konto WORLDIVES z urządzenia, którego wcześniej nie widzieliśmy: {device}, {when}.',
   'Hallo {first_name}, iemand heeft zich aangemeld op je WORLDIVES-account vanaf een apparaat dat we nog niet kenden: {device}, op {when}.',
   '{first_name}，你好！有人从一个我们从未见过的设备登录了你的 WORLDIVES 账户：{device}，时间 {when}。'],
 'Ciudad aproximada: {city}.': ['Approximate city: {city}.', 'Ville approximative : {city}.', 'Ungefähre Stadt: {city}.', 'Città approssimativa: {city}.', 'Cidade aproximada: {city}.', 'Przybliżone miasto: {city}.', 'Geschatte stad: {city}.', '大致城市：{city}。'],
 'Si has sido tú, no tienes que hacer nada. Si no, cambia tu contraseña ahora y cierra ese dispositivo en «Dispositivos conectados».':
  ['If it was you, you do not need to do anything. If not, change your password now and sign that device out in "Connected devices".',
   "Si c'était vous, vous n'avez rien à faire. Sinon, changez votre mot de passe maintenant et déconnectez cet appareil dans « Appareils connectés ».",
   'Wenn du das warst, musst du nichts tun. Wenn nicht, ändere jetzt dein Passwort und melde das Gerät unter „Verbundene Geräte“ ab.',
   'Se sei stato tu, non devi fare nulla. Altrimenti cambia subito la password e disconnetti quel dispositivo in «Dispositivi connessi».',
   'Se foste tu, não tens de fazer nada. Se não, muda já a tua palavra-passe e termina a sessão nesse dispositivo em «Dispositivos ligados».',
   'Jeśli to Ty, nie musisz nic robić. Jeśli nie, zmień teraz hasło i wyloguj to urządzenie w „Połączone urządzenia”.',
   'Was jij het, dan hoef je niets te doen. Zo niet, wijzig nu je wachtwoord en meld dat apparaat af bij "Verbonden apparaten".',
   '如果是你本人，无需任何操作。如果不是，请立即修改密码，并在「已连接的设备」中将该设备退出登录。'],
 'Ver dispositivos conectados': ['See connected devices', 'Voir les appareils connectés', 'Verbundene Geräte ansehen', 'Vedi i dispositivi connessi', 'Ver dispositivos ligados', 'Zobacz połączone urządzenia', 'Verbonden apparaten bekijken', '查看已连接的设备'],
 '{city_text}': ['{city_text}'] * 8,
}

# The app's own screens (es, en, fr): the lock, the PIN, the end of the session and Ajustes.
APP = {
 'WORLDIVES está bloqueada': ['WORLDIVES is locked', 'WORLDIVES est verrouillée'],
 'Escribe tu PIN de la app.': ['Enter your app PIN.', "Saisissez le code PIN de l'application."],
 'Desbloquéala con tu huella o con el código del móvil.': ["Unlock it with your fingerprint or your phone's code.", 'Déverrouillez-la avec votre empreinte ou le code du téléphone.'],
 'Desbloquear': ['Unlock', 'Déverrouiller'],
 'Desbloquear WORLDIVES': ['Unlock WORLDIVES', 'Déverrouiller WORLDIVES'],
 'Huella, cara o el código del móvil': ["Fingerprint, face or the phone's code", 'Empreinte, visage ou code du téléphone'],
 'Cerrar sesión en este móvil': ['Sign out on this phone', 'Se déconnecter sur ce téléphone'],
 'Toca otra vez: se cierra la sesión y se borran los datos de este móvil': ["Tap again: you are signed out and this phone's data are deleted", 'Touchez à nouveau : la session est fermée et les données de ce téléphone sont effacées'],
 'Usa tu huella o el código del móvil: el desbloqueo facial de este móvil no basta.': ["Use your fingerprint or the phone's code: this phone's face unlock is not enough.", 'Utilisez votre empreinte ou le code du téléphone : le déverrouillage facial de ce téléphone ne suffit pas.'],
 'PIN incorrecto.': ['Wrong PIN.', 'Code PIN incorrect.'],
 'Intentos que quedan': ['Attempts left', 'Tentatives restantes'],
 'Intentos fallidos': ['Failed attempts', 'Tentatives échouées'],
 'Borrar': ['Delete', 'Effacer'],
 'Sesión cerrada': ['Signed out', 'Session fermée'],
 'Entrar con mi contraseña': ['Sign in with my password', 'Me connecter avec mon mot de passe'],
 'Has fallado 5 veces. Por seguridad hemos cerrado la sesión y borrado los datos guardados en este móvil.':
  ['You failed 5 times. For security we have signed you out and deleted the data saved on this phone.',
   'Vous avez échoué 5 fois. Par sécurité, nous avons fermé la session et effacé les données enregistrées sur ce téléphone.'],
 'Tu sesión en este móvil se ha cerrado (desde «Dispositivos conectados», por un cambio de contraseña o por el titular del centro). Hemos borrado los datos guardados en el móvil.':
  ['Your session on this phone was closed (from "Connected devices", by a password change or by the owner of the centre). We have deleted the data saved on the phone.',
   'Votre session sur ce téléphone a été fermée (depuis « Appareils connectés », par un changement de mot de passe ou par le titulaire du centre). Nous avons effacé les données enregistrées sur le téléphone.'],
 'Han pasado 30 días desde que entraste en este móvil: vuelve a entrar con tu contraseña.': ['30 days have passed since you signed in on this phone: sign in again with your password.', 'Cela fait 30 jours que vous vous êtes connecté sur ce téléphone : reconnectez-vous avec votre mot de passe.'],
 'Has cerrado la sesión en este móvil.': ['You have signed out on this phone.', 'Vous vous êtes déconnecté sur ce téléphone.'],
 'Tu sesión en este móvil ha terminado.': ['Your session on this phone has ended.', 'Votre session sur ce téléphone est terminée.'],
 'Protege WORLDIVES': ['Protect WORLDIVES', 'Protégez WORLDIVES'],
 'Confirma con tu huella o con el código del móvil': ["Confirm with your fingerprint or your phone's code", 'Confirmez avec votre empreinte ou le code du téléphone'],
 'Protege tu cuenta': ['Protect your account', 'Protégez votre compte'],
 'Las cuentas profesionales se abren con tu huella o con el código del móvil. Vuelve a intentarlo.': ["Professional accounts open with your fingerprint or your phone's code. Try again.", 'Les comptes professionnels s\'ouvrent avec votre empreinte ou le code du téléphone. Réessayez.'],
 'Intentar de nuevo': ['Try again', 'Réessayer'],
 'Sin desbloqueo no se puede usar la cuenta profesional en este móvil.': ['Without unlocking, the professional account cannot be used on this phone.', 'Sans déverrouillage, le compte professionnel ne peut pas être utilisé sur ce téléphone.'],
 'Crea tu PIN de la app': ['Create your app PIN', "Créez le code PIN de l'application"],
 'Este móvil no tiene bloqueo de pantalla: WORLDIVES se abrirá con un PIN de 6 números. No lo compartas.': ['This phone has no screen lock: WORLDIVES will open with a 6-digit PIN. Do not share it.', "Ce téléphone n'a pas de verrouillage d'écran : WORLDIVES s'ouvrira avec un code PIN à 6 chiffres. Ne le partagez pas."],
 'Repite el PIN': ['Repeat the PIN', 'Répétez le code PIN'],
 'Los dos PIN no coinciden. Empieza de nuevo.': ['The two PINs do not match. Start again.', 'Les deux codes PIN ne correspondent pas. Recommencez.'],
 'Desde esta versión, la app de los centros y los profesionales se abre con tu huella o con un PIN. Vuelve a entrar con tu contraseña para activarlo.':
  ['From this version, the app for centres and professionals opens with your fingerprint or a PIN. Sign in again with your password to switch it on.',
   "Depuis cette version, l'application des centres et des professionnels s'ouvre avec votre empreinte ou un code PIN. Reconnectez-vous avec votre mot de passe pour l'activer."],
 'Entrar de nuevo': ['Sign in again', 'Se reconnecter'],
 # Ajustes
 'Seguridad': ['Security', 'Sécurité'],
 'Bloqueo de la app': ['App lock', "Verrouillage de l'application"],
 'PIN de la app (6 números)': ['App PIN (6 digits)', "Code PIN de l'application (6 chiffres)"],
 'Sin bloqueo': ['No lock', 'Sans verrouillage'],
 'se activa al volver a entrar': ['switched on when you sign in again', "s'active à la prochaine connexion"],
 'Siempre activado en las cuentas de centros y profesionales.': ['Always on for centre and professional accounts.', 'Toujours activé pour les comptes des centres et des professionnels.'],
 'Pide tu huella o el código al abrir la app y al volver después de 5 minutos.': ['Asks for your fingerprint or code when opening the app and when coming back after 5 minutes.', "Demande votre empreinte ou le code à l'ouverture de l'application et au retour après 5 minutes."],
 'Dispositivos conectados': ['Connected devices', 'Appareils connectés'],
 'Dónde está abierta tu cuenta y cerrar sesión a distancia': ['Where your account is open, and signing out remotely', 'Où votre compte est ouvert, et déconnexion à distance'],
 'Solo en Pruebas': ['Only in Pruebas', 'Uniquement dans Pruebas'],
 'bloqueo tras': ['lock after', 'verrouillage après'],
 'intentos fallidos': ['failed attempts', 'tentatives échouées'],
 'No se ha podido cambiar el bloqueo.': ['The lock could not be changed.', "Le verrouillage n'a pas pu être modifié."],
 'Bloqueo activado.': ['Lock switched on.', 'Verrouillage activé.'],
 'Bloqueo desactivado.': ['Lock switched off.', 'Verrouillage désactivé.'],
}


def ok(es, tr):
    return sorted(re.findall(r'\{\w+\}', es)) == sorted(re.findall(r'\{\w+\}', tr))


def main():
    for table, n in ((WEB, 8), (EMAIL, 8), (APP, 2)):
        for k, v in table.items():
            assert len(v) == n, k
            for tr in v: assert ok(k, tr), (k, tr)
    datos = ROOT / 'scripts' / 'idiomas' / 'datos'
    (datos / 'web_v50_55_seguridad.json').write_text(json.dumps({'exact': {es: dict(zip(LANGS, v)) for es, v in WEB.items()}, 'patterns': {}},
                                                                ensure_ascii=False, indent=1), encoding='utf-8')
    for i, lang in enumerate(LANGS):
        f = ROOT / 'app' / 'emails' / f'{lang}.json'
        pack = json.loads(f.read_text(encoding='utf-8'))
        for es, v in EMAIL.items(): pack.setdefault(es, v[i])
        f.write_text(json.dumps(dict(sorted(pack.items())), ensure_ascii=False, indent=1), encoding='utf-8')
    (datos / 'app_v50_55_seguridad.json').write_text(json.dumps(APP, ensure_ascii=False, indent=1), encoding='utf-8')
    print('ok', len(WEB), 'web,', len(EMAIL), 'correo,', len(APP), 'app')


if __name__ == '__main__':
    sys.exit(main())
