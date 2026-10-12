# Lista de lanzamiento

Versión v50.38 · 11/10/2026
Estado: borrador para revisión

Casillas para poner WORLDIVES DISCOVERY en producción. Cada punto se puede comprobar: dice **qué** hacer y **cómo** saber que está hecho.

Guías de apoyo:

- `docs/despliegue/README.md` (servidor, copias, correo y monitorización);
- `docs/mapas.md`;
- `docs/notas-de-version/v50.31.md` … `docs/notas-de-version/v50.38.md`;
- `docs/legal/inventario.md` (estado de cada punto y discrepancias).

Marcas:

- **[PENDIENTE ABOGADO]**: decisión jurídica.
- **[PENDIENTE GESTORÍA]**: tema fiscal o administrativo.
- **[PENDIENTE TITULAR]**: decisión de negocio.

Rellena la fecha y quién lo hizo al marcar cada casilla.

---

## 1. Titular y datos legales

- [ ] Elegir la forma jurídica del titular (autónomo o sociedad) **[PENDIENTE GESTORÍA]**.
- [ ] En *Administración → Legal*, rellenar todos los campos de `LEGAL_FIELDS`: titular, nombre comercial, NIF/CIF, domicilio, email de contacto, teléfono, datos registrales (si es sociedad), email de protección de datos y proveedor de alojamiento.
  - Comprobar: el pie de la web (`#footer-owner`) y `#/legal/aviso-legal` muestran los datos reales, sin ningún `{{…}}` ni «[pendiente de completar]».
- [ ] Revisar `#/legal/aviso-legal`, `#/legal/privacidad`, `#/legal/cookies`, `#/legal/condiciones-buceadores`, `#/legal/condiciones-reserva`, `#/legal/condiciones-centros`, `#/legal/normas-resenas`, `#/legal/clasificacion`, `#/legal/puntos`, `#/legal/accesibilidad`, `#/legal/contacto`, `#/legal/creditos`, `#/legal/denuncias` y `#/legal/seguridad`, en castellano y en inglés (los dos idiomas oficiales).
- [ ] Registro de actividades de tratamiento completo (`docs/legal/registro-actividades-tratamiento.md`), con los datos del titular.
- [ ] Anexo de encargado del tratamiento (`docs/legal/anexo-encargado-tratamiento.md`) revisado e incorporado a las condiciones para centros.
- [ ] Procedimiento de brechas (`docs/legal/procedimiento-brechas.md`): nombre y teléfono de quien decide y notifica a la AEPD en 72 h.
- [ ] Buzón de denuncias y de protección de datos operativo: enviar un correo de prueba a las direcciones publicadas y comprobar que llegan.
- [ ] Decidir la etiqueta única para la visibilidad pagada: «Patrocinado» (la que usa hoy la web) o «Destacado» **[PENDIENTE TITULAR]**.
- [ ] Registrar la marca y el dominio a nombre del titular (opcional, recomendable) **[PENDIENTE TITULAR]**.

## 2. Abogado

- [ ] Papel de cada parte en protección de datos: WORLDIVES como responsable o encargado frente a los datos de clientes que gestiona el centro (reservas manuales, importación CSV, «Solicitar información», feed iCal) **[PENDIENTE ABOGADO]**.
- [ ] Datos de salud: la web no admite certificados médicos (`clean_document_type`), pero sí guarda campos opcionales (fecha de nacimiento, contacto de emergencia, lastre). Confirmar los textos y la base legal **[PENDIENTE ABOGADO]**.
- [ ] Viajes y experiencias: confirmar que, con un solo proveedor por experiencia, no se aplica la normativa de viajes combinados **[PENDIENTE ABOGADO]**.
- [ ] Ley aplicable y consumidores extranjeros; ausencia de desistimiento (art. 103.l TRLGDCU) en el bloque legal de la reserva **[PENDIENTE ABOGADO]**.
- [ ] Responsabilidad del intermediario, señal, cancelaciones y devoluciones propuestas que el centro no hace: decidir qué hace WORLDIVES además del recordatorio a las 72 h y la incidencia **[PENDIENTE ABOGADO]** **[PENDIENTE TITULAR]**.
- [ ] Reglamento de Servicios Digitales (2022/2065): procedimiento de denuncias y recurso, y régimen de pequeñas empresas **[PENDIENTE ABOGADO]**.
- [ ] Catálogo: origen de la lista de 215 puntos y derecho *sui generis* (`docs/legal/catalogo-origen.md`) **[PENDIENTE ABOGADO]**.
- [ ] Términos de ArcGIS Location Platform: servir teselas por proxy, atribución y caché de 24 h en el navegador **[PENDIENTE ABOGADO]**.
- [ ] Puntos: texto «Cómo funcionan los puntos» como programa de fidelización sin valor monetario **[PENDIENTE ABOGADO]**.
- [ ] Consentimiento comercial y pie de los correos (LSSI art. 21, RGPD) **[PENDIENTE ABOGADO]**.
- [ ] Accesibilidad: obligaciones de la Ley 11/2023 para servicios de comercio electrónico **[PENDIENTE ABOGADO]**.
- [ ] Plazos de conservación de `RETENTION_DEFAULTS` (cuentas inactivas 36 meses, documentos caducados 12, avisos 24, registro de actividad 12) y conservación de reservas y pagos durante 6 años **[PENDIENTE ABOGADO]**.
- [ ] Publicar en *Administración → Legal* las versiones definitivas que salgan de la revisión.

## 3. Gestoría

- [ ] Alta censal (036/037) y epígrafe de la actividad **[PENDIENTE GESTORÍA]**.
- [ ] IVA de la cuota anual: España, UE (B2B con NIF-IVA e inversión del sujeto pasivo) y fuera de la UE. Decidir si los precios de *Administración → Planes* se muestran con IVA o sin él **[PENDIENTE GESTORÍA]**.
- [ ] Facturas de la cuota y Verifactu: hoy la web registra el pago (`plan_payments`) pero **no emite factura**. Decidir el programa de facturación y cómo se enlaza **[PENDIENTE GESTORÍA]**.
- [ ] DAC7: confirmar si WORLDIVES es «operador de plataforma» obligado aunque no cobre a través de la plataforma (cargos directos). Revisar el modelo 238 (y el 040 de alta), el plazo de enero y el formato del CSV de *Administración → Planes → Informe DAC7* **[PENDIENTE GESTORÍA]**.
- [ ] Justificante de reserva (no es factura): confirmar los datos fiscales mínimos del prestador que deben aparecer **[PENDIENTE GESTORÍA]**.

## 4. Servidor y dominio

- [ ] Contratar un VPS en la UE (Debian 12 o Ubuntu 24.04, mínimo 2 vCPU y 4 GB de RAM, SSD de 40 GB más el mapa base). Un alojamiento compartido no sirve.
- [ ] Crear el usuario `worldives`, clonar en `/opt/worldives`, crear el `.venv` e instalar `requirements.txt` (`docs/despliegue/README.md` §1).
- [ ] Python 3.11 o superior: `python3 --version`.
- [ ] Apuntar el DNS del dominio (A/AAAA) al VPS. Crear también `pruebas.<dominio>`.
- [ ] Caddy (`docs/despliegue/Caddyfile`) o nginx con certbot (`docs/despliegue/nginx.conf`). Comprobar: `https://<dominio>` con certificado válido y `http://` redirige a https.
- [ ] `/tiles/` sin compresión ni búfer en el proxy (está en los ejemplos de `docs/despliegue/`).
- [ ] `.env` en `/opt/worldives/.env` con `chmod 600` y propietario `worldives`. Mínimo:
  - `WOD_ENV=production`;
  - `WOD_PUBLIC_URL=https://…`;
  - `WOD_SECRET_KEY` (64 caracteres);
  - `WOD_HOST=127.0.0.1`, `WOD_PORT`;
  - `WOD_TRUSTED_PROXIES=127.0.0.1`;
  - `WOD_WORKERS` = número de núcleos;
  - `WOD_DB_PATH`, `WOD_BACKUP_DIR`, `WOD_BACKUP_COMMAND`.
- [ ] Servicio systemd: `docs/despliegue/worldives.service` con `systemctl enable --now worldives`. Comprobar: `systemctl status worldives` activo y `journalctl -u worldives` sin «No se puede arrancar en producción».
- [ ] Revisar los avisos de arranque (`production_warnings()`): SMTP, Stripe, mapa base y satélite. Todos resueltos o aceptados.
  - Atención: el aviso de falta de `STRIPE_CONNECT_WEBHOOK_SECRET` solo aparece si hay `ARCGIS_API_KEY`. Compruébalo a mano.
- [ ] Entorno de pruebas separado: `/opt/worldives-pruebas`, `docs/despliegue/worldives-pruebas.service`, `WOD_PORT=8001`, claves de **prueba** de Stripe y protección por contraseña.
- [ ] Ajustar `WOD_SOCKET_TIMEOUT` y `WOD_MAX_CONCURRENT` solo si la prueba de carga lo aconseja.

## 5. Seguridad

- [ ] `WOD_ALLOW_SETUP` sin definir (el servidor no arranca en producción con `=1`).
- [ ] `WOD_ADMIN_TOTP_REQUIRED=1`: valor por defecto y obligatorio en producción.
- [ ] Cortafuegos: solo 22 (SSH con clave, sin contraseña), 80 y 443. El puerto de la app (8000) no se ve desde fuera: probar `curl http://<ip>:8000` desde otra máquina y debe fallar.
- [ ] Actualizaciones automáticas de seguridad del sistema (`unattended-upgrades`).
- [ ] Comprobar las cabeceras en producción: `curl -sI https://<dominio>/` debe dar `Content-Security-Policy`, `Strict-Transport-Security`, `X-Frame-Options: DENY` y `X-Content-Type-Options: nosniff`.
- [ ] Comprobar que un POST sin `Origin` da 403 (CSRF, G10): `curl -X POST https://<dominio>/api/auth/login -d '{}'`.
- [ ] Comprobar que `https://<dominio>/api/health` devuelve solo `{"ok": true, "version": …}`.
- [ ] Ningún secreto en el repositorio: el CI (`.github/workflows/security-test.yml`) busca `sk_live`, `whsec_` y claves de ArcGIS. Debe pasar en verde.
- [ ] `WOD_EMBED_DOMAINS` con solo los proveedores de vídeo que se van a usar.
- [ ] Ejecutar `python app/server.py --report-center-accounts` en la base de producción: no debe haber cuentas de centro sin solicitud aprobada.

## 6. Correo (SPF, DKIM y DMARC)

- [ ] Elegir proveedor SMTP (recomendado Brevo) **[PENDIENTE TITULAR]**.
- [ ] `.env`: `WOD_SMTP_HOST`, `WOD_SMTP_PORT`, `WOD_SMTP_SECURITY`, `WOD_SMTP_USER`, `WOD_SMTP_PASSWORD`, `WOD_MAIL_FROM` (del dominio autenticado), `WOD_MAIL_FROM_NAME` y, si se usa, `WOD_MAIL_REPLY_TO`.
- [ ] DNS: **un solo** registro SPF con el `include` del proveedor.
- [ ] DNS: DKIM del proveedor.
- [ ] DNS: código de verificación del proveedor.
- [ ] DNS: DMARC en `p=none` con `rua`. Pasar a `quarantine` tras 2–4 semanas sin fallos y después a `reject`.
- [ ] *Administración → Correos → correo de prueba*: llega a Gmail y a Outlook, fuera de spam. En mail-tester.com, SPF, DKIM y DMARC salen «pass».
- [ ] Revisar en *Administración → Correos* las plantillas en es y en, con datos de ejemplo.
- [ ] La cola (`email_outbox`) queda vacía tras el arranque: nada en `failed`.

## 7. Stripe

**Cuenta de plataforma (cuota de los planes)**

- [ ] Cuenta Stripe del titular verificada (identidad, cuenta bancaria y datos fiscales).
- [ ] Connect activado en la cuenta. Cuentas conectadas con propiedades de controlador: panel completo (`WOD_STRIPE_DASHBOARD=full`), comisiones a cargo de la cuenta (`WOD_STRIPE_FEES_PAYER=account`), pérdidas a cargo de Stripe (`WOD_STRIPE_LOSSES=stripe`) y capacidad `card_payments`.
- [ ] Revisar en Stripe la responsabilidad por saldos negativos y las condiciones de Connect **[PENDIENTE ABOGADO]**.

**Webhooks (dos endpoints, dos secretos)**

- [ ] Endpoint de **plataforma**: `https://<dominio>/api/payments/webhook`, con `STRIPE_WEBHOOK_SECRET`. Eventos: `checkout.session.completed`, `checkout.session.async_payment_succeeded`, `checkout.session.expired`, `checkout.session.async_payment_failed`.
- [ ] Endpoint de **Connect** («eventos de cuentas conectadas»): `https://<dominio>/api/payments/webhook/connect`, con `STRIPE_CONNECT_WEBHOOK_SECRET`. Eventos:
  - `account.updated`, `account.application.deauthorized`;
  - `checkout.session.completed`, `checkout.session.async_payment_succeeded`, `checkout.session.expired`, `checkout.session.async_payment_failed`;
  - `payment_intent.payment_failed`;
  - `charge.refunded`, `refund.created`, `refund.updated`, `charge.refund.updated`;
  - `charge.dispute.created`, `charge.dispute.closed`.
- [ ] Comprobar: «Enviar evento de prueba» desde el panel de Stripe en los dos endpoints. Debe responder 200 `{"received": true}`.

**Claves live**

- [ ] `STRIPE_SECRET_KEY=sk_live_…` solo en el `.env` de producción. En pruebas, `sk_test_…`.
- [ ] Prueba real de punta a punta con una tarjeta propia y un centro de prueba aprobado:
  - reserva «Pago al reservar»;
  - el pago llega a la cuenta conectada del centro, no a la plataforma;
  - devolución parcial desde el panel del centro;
  - el justificante PDF identifica al prestador.
- [ ] Prueba real de la cuota anual: pago con Stripe en la cuenta de la plataforma y el plan se prorroga (`plan_payments`).

## 8. Mapas

- [ ] Instalar `pmtiles` y extraer el mapa base (`docs/mapas.md` §1): `pmtiles extract … data/tiles/worldives.pmtiles --maxzoom=14`, o 12 si el disco es pequeño.
- [ ] `.env`: `WOD_PMTILES_URL=/tiles/worldives.pmtiles` y `WOD_PMTILES_MAXZOOM` igual al nivel extraído.
  - Comprobar: *Administración → Mapas* muestra el tamaño del archivo y el mapa público tiene fondo.
- [ ] Cuenta de ArcGIS Location Platform y clave con permiso «Basemaps» en `ARCGIS_API_KEY`.
  - Comprobar: la capa «Satélite» aparece y el contador de *Administración → Mapas* sube.
- [ ] Límite mensual de teselas satélite (`maps_satellite_limit`, 1 900 000 por defecto, por debajo de las 2 000 000 gratuitas) revisado según el plan de ArcGIS.
- [ ] GEBCO: la capa «Relieve marino» carga y muestra su atribución.
- [ ] `#/legal/creditos` muestra las atribuciones de OSM, Esri y GEBCO.
- [x] El editor de centros de *Administración → Centros* usa el mismo mapa base que el resto de la web (corregido en v50.38; antes cargaba `tile.openstreetmap.org`).
- [ ] Recordatorio: actualizar el PMTiles cada 3–6 meses.

## 9. Base de producción y primer administrador con TOTP

- [ ] Crear la base limpia: `sudo -u worldives .venv/bin/python scripts/crear_semilla.py --source data/demo/catalogo-demo.sqlite3 --out /opt/worldives/data/worldives.sqlite3`.
  - Comprobar con `sqlite3`: 0 usuarios, 0 centros, 0 reservas, 0 pagos y 0 mensajes.
- [ ] Crear el primer admin: `sudo -u worldives .venv/bin/python app/server.py --create-admin`.
- [ ] Entrar como admin y **activar la verificación en dos pasos** (obligatoria). Guardar los códigos de recuperación fuera del servidor (gestor de contraseñas).
- [ ] Comprobar: sin TOTP, el admin no puede usar *Administración*.
- [ ] Revisar *Administración → Funciones*: interruptores (Puntos, Promociones, Experiencias, Patrocinio, Reseñas y Pagos online) y **modo piloto** si el alta de centros va a ser solo por invitación.
- [ ] Revisar los plazos de conservación en *Administración → Legal* (tarjeta de plazos, `/api/admin/retention`).
- [ ] Producción **sin** `WOD_DEMO_MODE`. La demo pública, si la hay, va en el entorno de pruebas con `WOD_DEMO_MODE=1` y centros ficticios (`scripts/herramientas/demo_centros_ficticios.py`).

## 10. Copias y prueba de restauración

- [ ] `WOD_BACKUP_DIR=/var/backups/worldives`, propiedad de `worldives`.
- [ ] Copia externa: `WOD_BACKUP_COMMAND=/opt/worldives/scripts/copia_externa.sh` con rclone hacia un almacenamiento en la UE, con versiones o bloqueo de objetos y **cifrado** (remoto `crypt`).
- [ ] Primera copia manual: `python app/server.py --backup-now`. Debe decir «Copia creada … ok» y sin «Copia externa fallida».
- [ ] *Administración → Operación* muestra la última copia de la base (cada hora) y de los archivos (cada día), y `quick_check` = ok.
- [ ] **Prueba de restauración** en el entorno de pruebas (`docs/despliegue/README.md` §7):
  - `--verify-backup <copia>`;
  - con el servicio parado, `--restore <copia> --yes`;
  - descomprimir `files/archivos-….tar.gz`;
  - arrancar y comprobar.
  - Fecha de la última prueba: ________
- [ ] Copia del `.env` y de los códigos de recuperación TOTP guardada fuera del servidor, con acceso limitado.

## 11. Monitor externo

- [ ] Monitor (UptimeRobot, Better Stack o Uptime Kuma) contra `https://<dominio>/api/health` cada 1–5 minutos, con aviso por email o móvil al titular.
- [ ] Probar la alerta: parar el servicio 5 minutos y comprobar que llega el aviso.
- [ ] Alertas de errores 500: `WOD_ALERT_ERRORS=5` y `WOD_ALERT_WINDOW_MIN=10`. Comprobar que el email del admin está verificado, porque las alertas (`ops_alert`, `notify_admins`) llegan por correo.
- [ ] Probar el banner de *Administración → Operación* (texto, nivel y horas) y quitarlo.

## 12. Catálogo

- [ ] Revisar las descripciones de los puntos en *Administración → Descripciones de puntos*:
  - marcar cada una como «Descripción revisada»;
  - completar «Datos que faltan» (sobre todo «qué se ve» en 256 puntos, acceso y profundidad).
  - Lista: `docs/legal/puntos-reescritos.md`.
- [ ] Confirmar el origen de los 215 puntos (ver Abogado) y verificar con fuentes propias o abiertas los que haga falta.
- [ ] Imágenes: el informe de *Administración → Imágenes de la web* (`images_report`) debe quedar sin «sin origen». Para cada imagen, registrar crédito y licencia, o sustituirla (`docs/legal/imagenes-origen.md`). `crear_base_produccion.py` no copia las fotos sin origen registrado.
- [ ] Destinos y experiencias de ejemplo: revisar textos e imágenes.
- [ ] Banda «Centros asociados»: decidir el mínimo de centros en *Administración → Patrocinio* (`partners_min_centers`, 6 por defecto) **[PENDIENTE TITULAR]**.
- [ ] Ningún centro PADI/SSI en producción: *Administración → Centros* empieza vacío.

## 13. Planes y precios

- [ ] Precios anuales de «Motor de reservas» y «Pro» en *Administración → Planes* (hoy sin definir) **[PENDIENTE TITULAR]**, con o sin IVA según la gestoría.
- [ ] Revisar las funciones y los límites de cada plan (propuesta por defecto en `PLAN_DEFAULTS`).
- [ ] Prueba gratuita: plan y días (`plans_trial_plan` = pro y `plans_trial_days` = 60 por defecto) **[PENDIENTE TITULAR]**.
- [ ] La página pública `#/planes` se ve bien en móvil y en ordenador, en es y en.
- [ ] Texto de las condiciones para centros alineado con los planes, la degradación a ficha gratuita y la ausencia de comisión.

## 14. Pruebas finales

- [ ] Suite automática en verde en el servidor de pruebas: `python3 -m unittest discover -s tests -p 'test_*.py'`.
  - A 11/10/2026 (v50.38), las 143 pruebas pasan en el entorno de desarrollo, también `test_phase8_languages.py`. Falta repetirlas en el servidor de pruebas.
- [ ] Recorridos en navegador: `tests/e2e_walk.py` (5 roles), `e2e_booking_modes.py`, `e2e_payments.py`, `e2e_points_email.py`, `e2e_legal_catalog.py`, `e2e_centers.py` y `e2e_markers.py`.
- [ ] Prueba de carga en el **servidor real** (entorno de pruebas, misma máquina): `python3 scripts/herramientas/prueba_carga.py --url https://pruebas.<dominio> --users 100 --seconds 60`. Anotar los resultados en `docs/despliegue/README.md` §9.
- [ ] Recorrido manual completo en producción con cuentas reales de prueba (borrarlas después):
  - alta de buceador con verificación de email;
  - alta de centro, aprobación con método y nota, prueba gratuita;
  - servicio y salida, reserva con pago y devolución;
  - reseña y respuesta del centro;
  - denuncia y resolución;
  - exportación ZIP y baja de la cuenta confirmada por email.
- [ ] Traducciones: el pase final en los 10 idiomas está hecho (v50.38). Falta la revisión jurídica al menos de es y en (oficiales) y que los nombres de botones citados en los textos traducidos coincidan con la web.
- [ ] Accesibilidad: navegación con teclado y lector de pantalla en portada, reserva y registro.
- [ ] Fecha de apertura y aviso a los centros piloto **[PENDIENTE TITULAR]**.
