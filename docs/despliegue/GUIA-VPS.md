# Instalar WORLDIVES DISCOVERY en Hostinger (VPS KVM 2, paquete de PRODUCCIÓN, v50.52)

Guía paso a paso para poner la web en **https://worldivesdiscovery.com** con el zip
`worldives-v50.54-PRODUCCION.zip`, según el encargo de despliegue del 14/10/2026. Cada paso termina con una
**comprobación**. Al final, `scripts/despliegue/comprobar_lanzamiento.py` revisa en el propio servidor toda la lista de
antes de abrir (paso 14).

Las órdenes que empiezan por `sudo` se escriben en el VPS (conectado por SSH). Lo que va entre `<…>` lo cambias tú.
**Claves y contraseñas: solo en los archivos del servidor que se indican y en tu gestor de contraseñas. Nunca en el
código, en el repositorio, en un correo ni en un chat.**

## 0. Antes de empezar

- La cuenta de Hostinger donde está el dominio `worldivesdiscovery.com` (se queda en Hostinger; solo se cambian sus DNS).
- Un **gestor de contraseñas** (Bitwarden, 1Password, KeePassXC…) para las claves del servidor.
- Una **clave SSH** en tu ordenador. Si no tienes, créala (Windows 10/11, macOS y Linux):

  ```bash
  ssh-keygen -t ed25519 -C "titular-worldives"      # Enter para la ruta; pon una frase de paso y guárdala en el gestor
  cat ~/.ssh/id_ed25519.pub                           # esta es la parte PÚBLICA: la que se pega en Hostinger
  ```

- La IP desde la que te conectarás (casa, oficina o VPN): la verás en https://ifconfig.me. El SSH solo se abrirá a ella.
- Más adelante: cuenta de **Better Stack** (paso 11) y un **destino de copias en la UE** fuera de Hostinger (paso 12;
  **Pendiente de decisión**: qué proveedor).

## 1. Contratar el VPS (KVM 2 en la UE)

En hPanel → **VPS** → contratar **KVM 2** (2 vCPU, 8 GB de RAM, 100 GB NVMe). En la configuración inicial:

| Opción | Qué elegir |
|---|---|
| **Ubicación** | **Alemania (Frankfurt)** o **Francia**. Nada en Reino Unido ni fuera de la UE. **No se puede cambiar después sin reinstalar**: revísalo antes de confirmar |
| Sistema | **Ubuntu 24.04 LTS** «limpio» (sin panel de control ni aplicaciones preinstaladas) |
| Clave SSH | Pega tu clave **pública** (`id_ed25519.pub`) |
| Contraseña de root | Una larga y aleatoria, guardada en el gestor (luego el acceso de root por SSH queda cerrado) |

**Comprobación:** hPanel → VPS → *Información general* muestra la ubicación elegida y la IP del VPS. Apunta la IP.

> Hostinger reduce la CPU de un VPS con uso alto sostenido. Si en la prueba de carga (paso 15) se nota, se sube a
> **KVM 4** desde hPanel sin perder datos.

## 2. DNS del dominio (en Hostinger)

hPanel → **Dominios** → `worldivesdiscovery.com` → **DNS / Nameservers**. Borra los registros `A`/`AAAA` antiguos de
`@` y `www` (los del alojamiento web o de «aparcado») y crea:

| Tipo | Nombre | Valor | TTL |
|---|---|---|---|
| A | `@` | IP del VPS | 3600 |
| A | `www` | IP del VPS | 3600 |
| A | `pruebas` | IP del VPS | 3600 |
| AAAA | `@`, `www`, `pruebas` | IPv6 del VPS (si la tiene) | 3600 |
| CAA | `@` | `0 issue "letsencrypt.org"` | 3600 |

No toques los registros del correo (MX, SPF, DKIM, DMARC): son del proveedor de correo (`docs/despliegue/README.md`,
apartado 10).

**Comprobación** (desde tu ordenador, puede tardar de minutos a unas horas): `nslookup worldivesdiscovery.com`,
`nslookup www.worldivesdiscovery.com` y `nslookup pruebas.worldivesdiscovery.com` devuelven la IP del VPS.

## 3. Acceso solo con clave SSH, sin root

```bash
ssh root@<IP-del-VPS>                                         # la primera vez, con tu clave
adduser <tu-usuario>                                          # tu usuario de administración (contraseña larga, al gestor)
usermod -aG sudo <tu-usuario>
rsync --archive --chown=<tu-usuario>:<tu-usuario> ~/.ssh /home/<tu-usuario>   # tu clave pasa a tu usuario
```

Abre **otra** terminal y comprueba que entras con `ssh <tu-usuario>@<IP-del-VPS>` y que `sudo -v` funciona. Solo
entonces cierra el acceso con contraseña y el de root:

```bash
sudo tee /etc/ssh/sshd_config.d/10-worldives.conf >/dev/null <<'EOF'
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin no
PubkeyAuthentication yes
EOF
sudo sshd -t && sudo systemctl restart ssh
```

**Comprobación:** `sudo sshd -T | grep -E '^(passwordauthentication|permitrootlogin|kbdinteractiveauthentication)'`
dice `no` en las tres, y `ssh root@<IP>` desde tu ordenador es rechazado.

## 4. Actualizaciones de seguridad automáticas

```bash
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades                # responde «Sí»
```

**Comprobación:** `cat /etc/apt/apt.conf.d/20auto-upgrades` muestra `APT::Periodic::Unattended-Upgrade "1";`.

## 5. Hora exacta y diario del sistema

```bash
sudo timedatectl set-timezone UTC          # el servidor en UTC; la web usa WOD_TIMEZONE para los centros
sudo timedatectl set-ntp true
sudo sed -i 's/^#\?MaxRetentionSec=.*/MaxRetentionSec=30day/' /etc/systemd/journald.conf && sudo systemctl restart systemd-journald
```

**Comprobación:** `timedatectl` dice `System clock synchronized: yes` y `NTP service: active` (ASVS V16.2.2).

## 6. Programas y la aplicación (desde el zip, nunca con `git clone`)

**Caddy desde su repositorio oficial**: el Caddy de Ubuntu 24.04 es la versión 2.6, que **no acepta** nuestro
`Caddyfile` (comprobado: falla en `basic_auth`); hace falta la 2.8 o posterior. Las órdenes son las de
https://caddyserver.com/docs/install#debian-ubuntu-raspbian (compruébalas allí):

```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update && sudo apt install -y caddy python3 python3-venv unzip rclone clamav clamav-daemon
caddy version                                                  # 2.8 o posterior
```

La aplicación (sube el zip desde tu ordenador con `scp worldives-v50.54-PRODUCCION.zip <tu-usuario>@<IP>:`):

```bash
sudo adduser --system --group --home /opt/worldives worldives
sudo mkdir -p /var/backups/worldives /var/log/worldives && sudo chown worldives: /var/backups/worldives
sudo unzip ~/worldives-v50.54-PRODUCCION.zip -d /opt/ && sudo mv /opt/worldives-v50.54-PRODUCCION/* /opt/worldives/
sudo rmdir /opt/worldives-v50.54-PRODUCCION && sudo chown -R worldives: /opt/worldives
cd /opt/worldives && sudo -u worldives python3 -m venv .venv && sudo -u worldives .venv/bin/pip install -r requirements.txt
```

**Comprobación:** `ls -a /opt/worldives` no tiene `.git` ni `CUENTAS-DEMO.txt` (V13.4.1).

## 7. Cortafuegos de entrada y salida (V13.2.5)

```bash
sudo SSH_DESDE="<tu-IP>" SMTP_PUERTO=587 bash /opt/worldives/scripts/despliegue/cortafuegos.sh
```

- Entrada: **22** (solo desde `SSH_DESDE`; puedes poner varias IP o redes separadas por espacios), **80** y **443**.
- Salida: **53** (DNS), **123** (hora), **67** (DHCP), **443** (Stripe, Better Stack, geocodificador, satélite,
  Meta/WhatsApp, Firebase, copias, Let's Encrypt, firmas del antivirus, actualizaciones), **80** (repositorios de Ubuntu,
  paquetes firmados) y el del **correo** (587 o 465). Qué datos recibe cada servicio: `docs/legal/inventario.md` §7.2.
- ufw filtra por puerto, no por nombre (las IP de Stripe o Meta cambian sin aviso). Además, el servicio de la web no
  puede conectarse a la red interna del proveedor (`IPAddressDeny` en `worldives.service`) y la web solo sale a
  direcciones públicas (`wod/remoto.py`).

**Mantén abierta la sesión SSH** y entra desde otra terminal antes de cerrarla. Si cambias de IP y te quedas fuera:
hPanel → VPS → *Terminal del navegador*, y vuelve a ejecutar el script con la IP nueva.

**Comprobación:** `sudo ufw status verbose` dice `Status: active` y `Default: deny (incoming), deny (outgoing)`.

## 8. Claves y `.env` (permisos 600)

```bash
cd /opt/worldives
sudo -u worldives cp .env.example .env && sudo chmod 600 .env && sudo chown worldives: .env
for k in WOD_SECRET_KEY WOD_DATA_KEY WOD_BACKUP_KEY; do echo "$k=$(python3 -c 'import secrets;print(secrets.token_urlsafe(48))')"; done
sudo -u worldives nano .env
```

Pega las tres claves que salen (nuevas, aleatorias, de 64 caracteres, distintas de las de pruebas) y **guárdalas en el
gestor de contraseñas**: sin `WOD_DATA_KEY` y `WOD_BACKUP_KEY` no se pueden abrir los teléfonos cifrados ni restaurar
una copia. Lo mínimo del `.env`:

```ini
WOD_ENV=production
WOD_PUBLIC_URL=https://worldivesdiscovery.com
WOD_SECRET_KEY=<clave 1>
WOD_DATA_KEY=<clave 2>
WOD_BACKUP_KEY=<clave 3>
WOD_TRUSTED_PROXIES=127.0.0.1
WOD_WORKERS=2                      # = vCPU del KVM 2
WOD_BACKUP_DIR=/var/backups/worldives
WOD_TIMEZONE=Europe/Madrid
WOD_AV_COMMAND=clamdscan --no-summary --fdpass -
```

`WOD_ADMIN_TOTP_REQUIRED` y `WOD_PAYMENTS_TOTP_REQUIRED` se dejan vacías (valen 1; en producción no se pueden apagar).
Correo, Stripe, satélite (`ARCGIS_API_KEY`), WhatsApp y avisos en el móvil: cada uno con sus variables cuando lo
actives (las explica `.env.example`).

**Comprobación:** `sudo stat -c '%a %U' /opt/worldives/.env` → `600 worldives`.

## 9. Administrador, servicio y HTTPS

### 9.1 Crear el administrador

Se hace **antes de arrancar el servicio** y siempre con el usuario del servicio (`worldives`), desde la carpeta de la
web. El comando lee el mismo `.env` y usa la misma base de datos que el servidor; si la base todavía no existe, la crea
con el catálogo de puntos de buceo (v50.54).

```bash
cd /opt/worldives
sudo -u worldives .venv/bin/python app/server.py --create-admin
```

Te pregunta el email, el usuario (propone la parte del email antes de la @; pulsa Intro para aceptarlo), el nombre y la
contraseña dos veces (no se ve al escribirla). La contraseña: **al menos 10 caracteres**, mejor una frase de cuatro
palabras («Coral-Faro-Morena-2026»); las muy conocidas o con el nombre de la web se rechazan. Debe salir algo así:

```text
WORLDIVES DISCOVERY · crear la cuenta de administración
Configuración: /opt/worldives/.env
Base de datos: /opt/worldives/data/worldivesdiscovery.sqlite3
Base nueva /opt/worldives/data/worldivesdiscovery.sqlite3 creada a partir de data/seed/catalogo.sqlite3.
Catálogo de especies: 31 especies de ejemplo.
Email del administrador: tu@worldivesdiscovery.com
Usuario para entrar [tu]:
Nombre y apellidos [Administración]: Tu Nombre
Contraseña (mínimo 10 caracteres; mejor una frase de varias palabras):
Repite la contraseña:
Hecho. Administrador creado: usuario «tu», email tu@worldivesdiscovery.com.
Siguiente paso: entra en https://worldivesdiscovery.com/#/login y activa la verificación en dos pasos (obligatoria para la administración).
```

También se puede dar todo en la misma línea (la contraseña se sigue pidiendo aparte):
`sudo -u worldives .venv/bin/python app/server.py --create-admin --email tu@worldivesdiscovery.com --username tu --name "Tu Nombre"`.

**Comprueba** que las dos primeras líneas dicen `/opt/worldives/.env` y la base de `/opt/worldives/data/`: si no, no
estás en la carpeta de la web o el `.env` no está en su sitio (paso 8).

### 9.2 Si da error

Si algo falla, el comando lo dice en una frase que empieza por «No se ha creado…» y **no cambia nada**. Repítelo
después de corregir el problema.

| Mensaje | Qué hacer |
|---|---|
| `No puedo abrir ni crear la base de datos (Permission denied…)` | Lo has ejecutado sin `sudo -u worldives` o la carpeta `data` no es de `worldives`: `sudo chown -R worldives: /opt/worldives/data` y repite con `sudo -u worldives`. |
| `el email no es válido` | Escribe el email completo, por ejemplo `tu@worldivesdiscovery.com`. |
| `el usuario debe tener de 3 a 40 letras…` | Usa solo letras, números, `.`, `_` o `-`, sin espacios. |
| `Las dos contraseñas no coinciden` | Repite el comando y escribe la misma dos veces. |
| `La contraseña debe tener al menos 10 caracteres` / `…demasiado fácil de adivinar` | Elige una frase larga que no uses en otro sitio. |
| `ya existe el administrador «…»` | Ya está creado: entra con él. Si no recuerdas la contraseña, usa el apartado 9.3. |
| `ya hay una cuenta (no administradora) con ese email o usuario` | Usa otro email o usuario para la administración. |
| `Aviso: esta base no tiene el catálogo de puntos de buceo` | La base se creó con `--create-admin` de una versión anterior (hasta v50.53), antes del primer arranque. Si todavía no hay datos reales, apártala **sin borrarla** y repite: `sudo -u worldives mv data/worldivesdiscovery.sqlite3 data/worldivesdiscovery.sqlite3.sin-catalogo` y otra vez `--create-admin`. Si ya tiene datos reales, no la toques y escríbenos. |
| `No such file or directory: '.venv/bin/python'` | Falta el paso 6 (entorno de Python) o no estás en `/opt/worldives`. |

### 9.3 He olvidado la contraseña del administrador

En el servidor, con el mismo usuario:

```bash
cd /opt/worldives
sudo -u worldives .venv/bin/python app/server.py --reset-admin-password                      # si solo hay un administrador
sudo -u worldives .venv/bin/python app/server.py --reset-admin-password --email tu@worldivesdiscovery.com   # si hay varios
```

Pide la contraseña nueva dos veces, cierra las sesiones abiertas de esa cuenta, quita el bloqueo por intentos fallidos
y queda anotado en el registro de actividad (`admin_password_reset_cli`). No hace falta parar el servicio. La
verificación en dos pasos sigue activa: al entrar te pide el código de la aplicación o uno de los códigos de
recuperación.

### 9.4 Servicio y HTTPS

```bash
sudo cp docs/despliegue/worldives.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now worldives
sudo cp docs/despliegue/Caddyfile /etc/caddy/Caddyfile
sudo caddy validate --config /etc/caddy/Caddyfile && sudo systemctl reload caddy
```

El bloque `pruebas.worldivesdiscovery.com` del `Caddyfile` lleva un hash de ejemplo: hasta el paso 13 esa dirección
pide una contraseña que nadie tiene, que es lo correcto.

Entra en https://worldivesdiscovery.com con el administrador: lo primero es activar la **verificación en dos pasos**
(obligatoria; sin ella solo llega a «Mi cuenta»). Guarda los códigos de recuperación en el gestor.

**Comprobación:**

```bash
curl -s -o /dev/null -w '%{http_code}\n' http://worldivesdiscovery.com/api/health      # 403 (la API nunca por http)
curl -s -o /dev/null -w '%{http_code} %{redirect_url}\n' https://www.worldivesdiscovery.com/centros   # 301 https://worldivesdiscovery.com/centros
curl -s https://worldivesdiscovery.com/api/health                                        # {"ok": true, "version": "50.52"}
echo | openssl s_client -connect worldivesdiscovery.com:443 -servername worldivesdiscovery.com 2>/dev/null | openssl x509 -noout -issuer   # Let's Encrypt
```

## 10. Antivirus (ClamAV, V5.4.3)

```bash
sudo systemctl enable --now clamav-freshclam      # descarga las firmas (la primera vez tarda unos minutos)
ls /var/lib/clamav                                # espera a ver main, daily y bytecode (.cvd o .cld)
sudo systemctl enable --now clamav-daemon         # clamd: unos 1–1,5 GB de RAM (con 8 GB hay margen)
sudo systemctl restart clamav-daemon              # Ubuntu no arranca clamd mientras no hay firmas
sudo systemctl restart worldives
```

Si `ls` no muestra las firmas pasados unos minutos, mira `sudo journalctl -u clamav-freshclam -n 30`. Un «403» o
«cool-down» quiere decir que el servidor oficial de ClamAV (`database.clamav.net`) ha frenado las descargas desde esa
IP durante un tiempo: freshclam lo vuelve a intentar solo. Espera y no lo cambies por un espejo no oficial. El
cortafuegos del paso 7 ya deja salir por el puerto 443, que es el que usa.

`WOD_AV_COMMAND` ya está en el `.env` (paso 8). Cada documento que suben buceadores y centros pasa por el antivirus
antes de guardarse; si encuentra algo, se rechaza y la administración recibe un aviso de seguridad.

**Comprobación:** *Administración → Operación → Estado del sistema*, fila **Antivirus de los documentos** en verde con
«Comprobado: detecta el archivo de prueba EICAR». Desde la v50.52 la fila prueba el antivirus de verdad con el archivo
de prueba estándar (EICAR, inofensivo): si clamd está parado o sin firmas, sale en rojo.

## 11. Registros fuera del servidor: Better Stack (región UE, V16.4.2 y V16.4.3)

Así los registros quedan fuera del VPS y quien entrara en él no podría borrar sus huellas.

1. **Cuenta** en https://betterstack.com a nombre de la SL (mientras no esté constituida, del titular), con la
   **verificación en dos pasos** activada. Plan gratuito para montarlo; **plan Nano en región UE (30 días)** antes de
   abrir al público.
2. **Fuente** (*Telemetry → Sources → Connect source*): nombre «WORLDIVES producción», plataforma **Vector**, región de
   datos **Europa (DE)**. Apunta el **token** de la fuente y su **«Ingesting host»**.
3. **Vector** en el VPS. Instálalo con el repositorio oficial de Vector (https://vector.dev/docs/setup/installation/package-managers/apt/;
   Better Stack también muestra las órdenes al crear la fuente) y configúralo:

   ```bash
   sudo install -m 600 -o root -g root /dev/null /etc/vector/betterstack.env
   sudo nano /etc/vector/betterstack.env          # BETTERSTACK_TOKEN=<token>  y  BETTERSTACK_HOST=<ingesting host>
   sudo mkdir -p /etc/systemd/system/vector.service.d
   # El token, desde su archivo; y permiso para LEER (no escribir) el registro de Caddy, que Caddy crea con permisos 600
   printf '[Service]\nEnvironmentFile=/etc/vector/betterstack.env\nAmbientCapabilities=CAP_DAC_READ_SEARCH\n' | sudo tee /etc/systemd/system/vector.service.d/betterstack.conf
   sudo cp /opt/worldives/docs/despliegue/vector.yaml /etc/vector/vector.yaml
   sudo usermod -aG systemd-journal vector          # leer el diario del servicio worldives
   sudo systemctl daemon-reload && sudo systemctl enable --now vector && sudo systemctl restart vector
   ```

   El token va en su propio archivo con permisos 600, **no** en el `.env` de la aplicación. Qué se envía (y nada más):
   los sucesos de seguridad y los inicios de sesión fallidos de la aplicación, y el registro de accesos de Caddy, tal
   como ya salen (UTC, sin testigos ni consultas, IP recortada). Detalle en `docs/seguridad/registros.md`.
4. **Alertas** (*Alerts* / *Monitors*, aviso por correo al titular). En el buscador de la fuente, cada una con su
   condición:

   | Alerta | Condición | Cómo probarla |
   |---|---|---|
   | Varios errores 500 seguidos | `servicio = caddy` y `estado >= 500`: 5 o más en 10 minutos | Para el servicio (`sudo systemctl stop worldives`): Caddy responde 502; vuelve a arrancarlo |
   | Pico de inicios de sesión fallidos o bloqueos | `tipo = login_failed`: 20 o más en 5 minutos; o `tipo` en `login_blocked`, `login_bruteforce` | Falla la contraseña varias veces desde el móvil con datos |
   | Firmas falsas de Stripe o WhatsApp | `tipo` en `stripe_bad_signature`, `webhook_bad_signature`, `integration_bad_key`: 1 o más | `curl -X POST https://worldivesdiscovery.com/api/payments/webhook -H 'Stripe-Signature: t=1,v1=00' -d '{}'` |
   | Accesos denegados repetidos de una cuenta | `tipo = access_denied` agrupado por `datos.usuario`: 10 o más en 10 minutos | Con una cuenta de buceador de prueba, abre varias veces `/api/admin/health` |
   | La web no responde | Monitor de disponibilidad (*Uptime*) sobre `https://worldivesdiscovery.com/api/health`, cada 3 minutos, que espere 200 y la palabra `ok` | Para el servicio un momento |

**Comprobación:** en *Live tail* de la fuente aparecen líneas `servicio: caddy` al abrir la web y `tipo: login_failed`
al fallar una contraseña; cada alerta de la tabla ha enviado su correo.

## 12. Copias fuera del servidor y restauración de prueba

Las copias se hacen solas (base de datos cada hora y archivos cada día, cifradas con `WOD_BACKUP_KEY`). Falta
mandarlas **fuera de Hostinger, en la UE**: el proveedor está **Pendiente de decisión** (por ejemplo Hetzner Storage Box
en Alemania o Finlandia, Backblaze B2 en Ámsterdam o Scaleway en Francia; mejor con versiones o bloqueo de objetos). No
te fíes solo de las copias semanales de Hostinger: están en el mismo proveedor.

```bash
sudo -u worldives rclone config                  # crea el remoto «externo» con los datos del proveedor
sudo -u worldives nano /opt/worldives/.env       # WOD_BACKUP_COMMAND=/opt/worldives/scripts/copia_externa.sh
sudo systemctl restart worldives
sudo -u worldives /opt/worldives/.venv/bin/python /opt/worldives/app/server.py --backup-now   # copia y envío ahora
sudo bash /opt/worldives/scripts/despliegue/restauracion_prueba.sh                         # restauración de prueba
```

La restauración de prueba descarga la última copia **del destino externo**, la descifra, la comprueba y la restaura en
una carpeta temporal (nunca sobre la base en uso, y sin arrancar nada con ella), compara cuántos usuarios, centros y
reservas tiene, y lo anota en `/var/log/worldives/restauracion.log`. Repítela una vez al mes.

**Comprobación:** el script termina con «Prueba de restauración correcta» y el *Estado del sistema* muestra la copia
externa en verde.

## 13. Entorno de pruebas: https://pruebas.worldivesdiscovery.com

Con el **mismo zip de PRODUCCIÓN** (nunca el de DEMO: el servidor se niega a arrancar en modo demo con este dominio o
sus subdominios), su propio usuario, carpeta, base, `.env` y copias, y detrás de una contraseña.

```bash
sudo adduser --system --group --home /opt/worldives-pruebas worldives-pruebas
sudo mkdir -p /var/backups/worldives-pruebas && sudo chown worldives-pruebas: /var/backups/worldives-pruebas
sudo unzip ~/worldives-v50.54-PRODUCCION.zip -d /tmp/wp && sudo mv /tmp/wp/worldives-v50.54-PRODUCCION/* /opt/worldives-pruebas/
sudo chown -R worldives-pruebas: /opt/worldives-pruebas
cd /opt/worldives-pruebas && sudo -u worldives-pruebas python3 -m venv .venv && sudo -u worldives-pruebas .venv/bin/pip install -r requirements.txt
sudo -u worldives-pruebas cp .env.example .env && sudo chmod 600 .env && sudo -u worldives-pruebas nano .env
```

En su `.env`: `WOD_ENV=production`, `WOD_PUBLIC_URL=https://pruebas.worldivesdiscovery.com`, `WOD_PORT=8001`,
**claves nuevas propias** (no las de producción), `WOD_BACKUP_DIR=/var/backups/worldives-pruebas`,
`WOD_AV_COMMAND` como en producción y **Stripe solo con claves de prueba** (`sk_test_…`). Después:

```bash
sudo -u worldives-pruebas .venv/bin/python app/server.py --create-admin
sudo cp docs/despliegue/worldives-pruebas.service /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable --now worldives-pruebas
caddy hash-password                                # escribe la contraseña del equipo (guárdala en el gestor) y copia el hash
sudo nano /etc/caddy/Caddyfile                     # bloque pruebas: «equipo <hash>»
sudo caddy validate --config /etc/caddy/Caddyfile && sudo systemctl reload caddy
```

**Comprobación:** `curl -s -o /dev/null -w '%{http_code}\n' https://pruebas.worldivesdiscovery.com/` → `401`; con
la contraseña, la web de pruebas. **Nunca se copian ahí datos reales.**

## 14. Comprobar la lista de antes de abrir

```bash
sudo python3 /opt/worldives/scripts/despliegue/comprobar_lanzamiento.py --markdown /root/lista-lanzamiento.md
```

Revisa en el servidor cada casilla del encargo (SSH, cortafuegos, HTTPS, antivirus, hora, `.env`, instalación limpia,
verificación en dos pasos del administrador, actualizaciones, copias externas, restauración, Better Stack, entorno de
pruebas y salida a internet del servicio) y marca **OK**, **FALLO** (con lo que falta) o **A MANO** (lo que no se puede
ver desde el servidor: ubicación del VPS, copia de las claves en el gestor, alertas, abogado, SL…). El archivo
`/root/lista-lanzamiento.md` es la lista con cómo se comprobó cada casilla. **No se abre el piloto hasta que no quede
ningún FALLO y todas las «A MANO» estén hechas** (`docs/despliegue/lista-lanzamiento.md`).

## 15. Prueba de carga y pago real

- **Carga** (contra pruebas, nunca contra producción): `tests/carga/` (`docs/auditoria/v50.51/carga.md`). Si el VPS se
  frena con la carga sostenida, KVM 4.
- **Pago real pequeño**: con Stripe en modo real en producción, un servicio de 1 €, reservar y pagar con una tarjeta
  propia, devolverlo desde la reserva y comprobar el aviso en *Administración → Pagos*.

## 16. Actualizar a una versión nueva sin perder datos

Los datos viven en `data/` (base de datos y fotos), `storage/` (documentos privados) y `.env`. El código nuevo nunca
los toca, y las migraciones solo añaden y transforman (guardan antes una copia completa si reescriben algo).

```bash
cd /opt
sudo -u worldives /opt/worldives/.venv/bin/python /opt/worldives/app/server.py --backup-now     # copia antes de actualizar
sudo unzip worldives-v<nueva>-PRODUCCION.zip -d /opt/nueva
sudo systemctl stop worldives
sudo cp -a /opt/worldives /opt/worldives-anterior                  # para volver atrás si hiciera falta
sudo rsync -a --exclude data/ --exclude storage/ --exclude .env --exclude .venv/ /opt/nueva/worldives-v<nueva>-PRODUCCION/ /opt/worldives/
sudo chown -R worldives: /opt/worldives
sudo -u worldives /opt/worldives/.venv/bin/pip install -r /opt/worldives/requirements.txt
sudo systemctl start worldives                                     # las migraciones se aplican solas al arrancar
```

Primero en pruebas (`/opt/worldives-pruebas`), luego en producción. Si algo va mal: `sudo systemctl stop worldives`,
vuelve a poner `/opt/worldives-anterior` en su sitio y arranca de nuevo.
