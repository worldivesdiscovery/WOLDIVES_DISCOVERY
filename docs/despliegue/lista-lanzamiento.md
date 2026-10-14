# Lista de comprobación antes de abrir el piloto (v50.52)

La lista del encargo de despliegue del 14/10/2026, casilla por casilla. **No se abre el modo piloto hasta que todas
estén marcadas.** La lista general de lanzamiento sigue en `docs/legal/lista-lanzamiento.md`.

Cómo leerla:

- **[x]** comprobado y correcto, y cómo se comprobó.
- **[ ]** todavía no se puede marcar: dice qué falta, quién lo hace y **cómo se comprobará**. Lo que se hace en el VPS
  lo comprueba en el propio servidor `sudo python3 /opt/worldives/scripts/despliegue/comprobar_lanzamiento.py
  --markdown /root/lista-lanzamiento.md` (paso 14 de `GUIA-VPS.md`), que escribe esta misma lista con OK, FALLO o
  A MANO y el detalle de cada casilla.
- «Preparado y probado» es lo que se entrega listo y probado en el entorno de desarrollo (no en el VPS, que aún no
  existe).

El VPS todavía no está contratado: **ninguna casilla de servidor, copias o registros puede estar marcada hoy**. Lo
que sí está hecho es todo lo que se necesita para marcarlas, probado.

## Servidor

- [ ] **VPS KVM 2 en Alemania o Francia, solo con clave SSH** — lo hace el titular (`GUIA-VPS.md`, pasos 1 y 3). Se
  comprueba: ubicación en hPanel (A MANO) y `sshd -T` con `passwordauthentication no`, `permitrootlogin no` y claves
  autorizadas (comprobador).
- [ ] **Cortafuegos de entrada y salida aplicado y documentado** — lo hace el titular con
  `scripts/despliegue/cortafuegos.sh` (paso 7). Preparado y probado: las reglas del script, con `ufw --dry-run`
  (entrada 22 desde las IP indicadas, 80 y 443; salida 53, 123, 67, 443, 80 y el puerto del correo; todo lo demás
  denegado); `IPAddressDeny` en el servicio verificado con `systemd-analyze verify`. Se comprueba: `ufw status verbose`
  y una conexión HTTPS de prueba con las mismas restricciones que el servicio (comprobador).
- [ ] **HTTPS con Let's Encrypt; `caddy validate` correcto; /api por http da 403** — paso 9. Preparado y probado: el
  `Caddyfile` valida con Caddy 2.8.4 y, en marcha, da 403 en `/api` por http (raíz y pruebas), 301 de `www` a la raíz
  por http y https, 401 en pruebas sin contraseña, HSTS y registro sin testigos ni IP completa. **Ojo**: el Caddy de
  Ubuntu 24.04 (2.6.2) **no** acepta el `Caddyfile` (comprobado); la guía instala el oficial. Se comprueba: emisor del
  certificado, `caddy validate`, códigos 403 y 301 (comprobador).
- [ ] **ClamAV activo y en verde en «Estado del sistema»** — paso 10. Preparado y probado: con clamd en marcha,
  `clamdscan --no-summary --fdpass -` detecta el archivo de prueba EICAR (código 1) y deja pasar uno limpio (0), también
  con el usuario del servicio; la fila del *Estado del sistema* solo sale en verde si lo detecta
  (`tests/test_v50_52_despliegue.py`). Se comprueba: la fila en verde y el comprobador (clamd, freshclam, firmas al día
  y EICAR detectado).
- [ ] **NTP sincronizado** — paso 5. Se comprueba: `timedatectl show -p NTPSynchronized --value` → `yes` (comprobador).
- [ ] **`.env` con permisos 600 y claves nuevas de producción; copia de las claves fuera del servidor** — paso 8. Se
  comprueba: permisos 600 y propietario `worldives`, las tres claves de 32 caracteres o más, distintas entre sí, de las
  de pruebas y de las de la demo, `WOD_ENV=production` y `WOD_PUBLIC_URL=https://worldivesdiscovery.com`
  (comprobador). La copia en el gestor de contraseñas: A MANO.
- [ ] **Instalado desde el zip de PRODUCCIÓN, sin `.git`, base limpia, admin creado con `--create-admin`** — pasos 6
  y 9. Preparado: el zip `worldives-v50.53-produccion.zip` pasa su comprobación automática (sin cuentas, claves ni
  datos de prueba). Se comprueba: sin `.git` ni restos de la demo, ninguna cuenta de prueba en la base y al menos un
  administrador (comprobador).
- [ ] **Verificación en dos pasos activada en la cuenta de administración** — paso 9. Se comprueba: todos los
  administradores con `totp_enabled=1` (comprobador). Además, en producción la web no deja usar la administración sin
  ella.

## Copias y registros

- [ ] **Copias externas funcionando y una restauración de prueba hecha** — paso 12; el proveedor de copias en la UE es
  **Pendiente de decisión** del titular. Preparado y probado: copia cifrada enviada con `scripts/copia_externa.sh` a un
  remoto de rclone y restaurada desde allí con `scripts/despliegue/restauracion_prueba.sh` (descarga, descifrado,
  comprobación de integridad, restauración en una carpeta temporal, recuento y anotación en el registro). Se comprueba:
  última copia externa de hace menos de 3 horas y restauración anotada en los últimos 35 días (comprobador).
- [ ] **Registros llegando a Better Stack (región UE) y alertas probadas** — paso 11; la cuenta la abre el titular.
  Preparado y probado: `docs/despliegue/vector.yaml` valida con Vector 0.43.1 y, de punta a punta contra un receptor
  local, envía solo los sucesos de seguridad, los inicios fallidos y el registro de Caddy, con el token como
  `Bearer`, y nunca emails, trazas ni testigos. Se comprueba: Vector activo, archivo del token con permisos 600 y
  `vector validate` (comprobador); las líneas en *Live tail* y cada alerta de la tabla del paso 11 (A MANO).

## Código

- [x] **Verificación en dos pasos obligatoria para centros con cobros, con sus pruebas** — `tests/test_v50_52_cobros_2fa.py`
  (11 pruebas, todas nombran V6.3.3): centro con Stripe y sin verificación no ve reservas, clientes, cobros ni
  exportaciones por ninguna ruta (barrido de todas las rutas del panel); miembro con «Cobros», igual; centro sin cobros
  online entra sin ella; los pagos de los clientes de un centro bloqueado se confirman (webhook de Stripe). Además:
  plazo de 14 días con aviso y correo, Stripe no se conecta sin ella, no se desactiva con cobros, registro en la
  actividad y producción se niega a apagarla. En un navegador real (`tests/navegador/e2e_cobros_2fa.py`): 20/20.
- [ ] **Batería completa en verde en un servidor de pruebas igual al real** — en este entorno, en verde (cifras en
  `docs/notas-de-version/v50.52.md`, «Comprobado»). Falta repetirla en `pruebas.worldivesdiscovery.com` cuando
  exista: `cd /opt/worldives-pruebas/tests && sudo -u worldives-pruebas ../.venv/bin/python -m unittest discover` y
  `../.venv/bin/python -m pytest test_v50_51_asvs.py`.
- [ ] **Prueba de carga en el VPS real** — contra pruebas, con `tests/carga/` (`docs/auditoria/v50.51/carga.md`).
  Si la CPU se frena con carga sostenida, KVM 4.
- [ ] **Reserva completa de punta a punta con pago real pequeño en Stripe y su devolución** — con `sk_live_` en
  producción: un servicio de 1 €, pagarlo con una tarjeta propia, devolverlo desde la reserva y ver el aviso de Stripe
  en *Administración → Pagos*.

## Legal y cuentas (las cierra el titular)

- [ ] **SL constituida y datos puestos en *Administración → Legal*** — también los dos campos nuevos (ubicación del
  servidor y destino de las copias); hasta entonces los textos dicen «[pendiente de completar]».
- [ ] **Stripe a nombre de la SL.**
- [ ] **Textos legales actualizados y revisados por un abogado** — actualizados (v50.52): política de privacidad,
  condiciones para centros, anexo de encargado, registro de actividades y procedimiento de brechas. Lista de cambios y
  preguntas: `docs/legal/cambios-v50.52-para-abogado.md`. Comprobado que ningún texto menciona la comisión del 10 %.
  Falta la revisión del abogado.

## Después del piloto, antes de abrir a todos

- [ ] **Prueba de intrusión independiente.**
- [ ] **Better Stack en plan de pago (30 días de retención)** — plan Nano, región UE; la política de privacidad ya dice
  30 días.
