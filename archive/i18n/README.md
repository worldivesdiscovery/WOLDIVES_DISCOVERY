# Idiomas retirados (v50.33)

Japonés (`ja`), coreano (`ko`) y chino tradicional (`zt`) dejaron de ofrecerse en la v50.33 por decisión del titular.
Sus archivos se guardan aquí, fuera de `public/`, por si se recuperan:

- `web/<idioma>.json`: textos de la interfaz.
- `emails/<idioma>.json`: textos de los correos.

Para recuperar uno: moverlo de nuevo a `public/assets/i18n/` y `app/emails/`, añadirlo a `LANGS` y `WD_LOCALES`
(`public/assets/js/world-dives-v8.js`), a `MAIL_LANGS` (`app/server.py`) y quitarlo de `LANG_RETIRED` y `normalize_lang`.
Los textos añadidos desde la v50.31 no están traducidos a estos idiomas.
