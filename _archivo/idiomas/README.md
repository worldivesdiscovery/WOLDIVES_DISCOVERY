# Idiomas retirados (v50.33)

Japonés (`ja`), coreano (`ko`) y chino tradicional (`zt`) dejaron de ofrecerse en la v50.33 por decisión del titular.
Sus archivos se guardan aquí, fuera de `public/`, por si se recuperan:

- `web/<idioma>.json`: textos de la interfaz.
- `emails/<idioma>.json`: textos de los correos.

Para recuperar uno: moverlo de nuevo a `public/assets/i18n/` y `app/emails/`, añadirlo a `LANGS` y `WD_LOCALES`
(`public/assets/js/world-dives-v8.js`), a `MAIL_LANGS` (`app/server.py`) y quitarlo de `LANG_RETIRED` y `normalize_lang`.
Los textos añadidos desde la v50.31 no están traducidos a estos idiomas.

## Ruso (v50.46)

El ruso (`ru`) se retira en la v50.46 por decisión del titular: en Rusia no se puede pagar con Stripe ni con tarjetas
Visa/Mastercard emitidas allí. Se guardan `web/ru.json`, `emails/ru.json` y los textos legales (`legal/ru/`). Quien lo
tenía elegido pasa a inglés, también en la cola de correos; si el navegador pide ruso, se usa inglés.
