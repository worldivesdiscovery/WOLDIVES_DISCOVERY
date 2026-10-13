# Instalar WORLDIVES DISCOVERY en un VPS (paquete de PRODUCCIÓN, v50.51)

Guía paso a paso con el zip `worldives-v50.51-PRODUCCION.zip`. Los detalles de cada parte (proxy, copias, correo,
rendimiento) están en `docs/despliegue/README.md`; los mapas, en `docs/mapas.md`.

**Antes de empezar necesitas:**
- el dominio (por ejemplo `worldives.com`), con acceso a su DNS;
- un VPS Linux (tamaño en el paso 1);
- las claves de los servicios que quieras activar ya (correo, Stripe, ArcGIS…). Ninguna es obligatoria para
  arrancar: lo que falte queda desactivado y aparece como «Pendiente» en *Administración → Operación → Estado del
  sistema*.

## 1. Servidor

| Uso | VPS recomendado |
|---|---|
| Lanzamiento y primeros meses (cientos de personas a la vez) | **4 vCPU, 8 GB de RAM, 80 GB SSD (NVMe)**, en la UE (Debian 12 o Ubuntu 24.04), `WOD_WORKERS=4` |
| 10.000 personas a la vez navegando con normalidad | 8 vCPU, 16 GB de RAM, NVMe, `WOD_WORKERS=8` |
| 10.000 personas a la vez con uso intenso | 32 vCPU, 32 GB de RAM, NVMe, `WOD_WORKERS=32` (16 vCPU dedicadas como mínimo, sin margen) |
| Mínimo para probar | 2 vCPU, 4 GB de RAM, 40 GB SSD |

`WOD_WORKERS` = número de núcleos. El cálculo sale de la prueba de carga de esta versión
(`docs/auditoria/v50.51/carga.md`): cuánta CPU gasta cada petición, cuándo conviene crecer y cuándo pasar a
PostgreSQL (solo para repartir la web en varios servidores).

## 2. Dominio

En el panel de tu proveedor de dominio crea dos registros que apunten a la IP del VPS:

| Tipo | Nombre | Valor |
|---|---|---|
| A | `@` (worldives.com) | IP del VPS |
| A | `www` | IP del VPS |

(Y los mismos con `AAAA` si el VPS tiene IPv6.) Los cambios de DNS tardan de minutos a unas horas.

## 3. Instalar

Conectado al VPS por SSH:

```bash
sudo apt update && sudo apt install -y python3 python3-venv unzip caddy
sudo adduser --system --group --home /opt/worldives worldives
sudo mkdir -p /var/backups/worldives && sudo chown worldives: /var/backups/worldives
# Sube el zip al servidor (por ejemplo con scp) y descomprímelo:
sudo unzip worldives-v50.51-PRODUCCION.zip -d /opt/ && sudo mv /opt/worldives-v50.51-PRODUCCION/* /opt/worldives/ && sudo chown -R worldives: /opt/worldives
cd /opt/worldives
sudo -u worldives python3 -m venv .venv && sudo -u worldives .venv/bin/pip install -r requirements.txt
```

## 4. Configuración (`.env`)

```bash
sudo -u worldives cp .env.example .env && sudo chmod 600 .env && sudo -u worldives nano .env
```

Cada variable del archivo lleva su explicación. Lo mínimo:

```ini
WOD_ENV=production
WOD_PUBLIC_URL=https://worldives.com
WOD_SECRET_KEY=        # python3 -c "import secrets;print(secrets.token_urlsafe(48))"
WOD_DATA_KEY=          # python3 -c "import secrets;print(secrets.token_urlsafe(32))"
WOD_BACKUP_KEY=        # python3 -c "import secrets;print(secrets.token_urlsafe(32))"
WOD_TRUSTED_PROXIES=127.0.0.1
WOD_WORKERS=4
WOD_BACKUP_DIR=/var/backups/worldives
```

**Guarda `WOD_DATA_KEY` y `WOD_BACKUP_KEY` también fuera del servidor** (en un gestor de contraseñas): sin ellas no
se pueden abrir los teléfonos cifrados ni restaurar una copia. Las claves y contraseñas solo van en este archivo,
nunca en el código ni en el chat.

Para activar más tarde cualquier servicio (correo, Stripe, satélite, WhatsApp, avisos en el móvil), rellena sus
variables y reinicia: `sudo systemctl restart worldives`.

## 5. Primera puesta en marcha y administrador

```bash
sudo -u worldives .venv/bin/python app/server.py --create-admin
```

Pide email, usuario, nombre y contraseña. La base de datos se crea sola la primera vez, a partir de
`data/seed/catalogo.sqlite3`, con el catálogo de puntos, los textos legales, los 9 idiomas y el catálogo de especies.
**No trae usuarios, centros ni reservas.** En la web real no hay pantalla para crear administradores: solo este
comando. Al entrar por primera vez, el administrador activa la verificación en dos pasos (obligatoria).

## 6. HTTPS con Let's Encrypt

Caddy obtiene y renueva el certificado solo:

```bash
sudo cp docs/despliegue/Caddyfile /etc/caddy/Caddyfile     # cambia worldives.com por tu dominio y borra el bloque de pruebas
sudo systemctl reload caddy
```

Si prefieres nginx, `docs/despliegue/nginx.conf` con `certbot --nginx`.

## 7. Arranque automático

```bash
sudo cp docs/despliegue/worldives.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now worldives
journalctl -u worldives -f        # ver qué pasa (Ctrl+C para salir)
```

El servicio se reinicia solo si se cae y al reiniciar el VPS.

Abre `https://worldives.com`, entra con el administrador y mira *Administración → Operación → Estado del sistema*:
cada servicio sale como **Configurado**, **Pendiente** (falta su clave; esa función está desactivada) o **Error**.

## 8. Copias de seguridad

Automáticas, sin configurar nada más:
- **base de datos cada hora**, comprobada y cifrada con `WOD_BACKUP_KEY`;
- **fotos y documentos cada día**;
- se guardan 48 copias horarias, una diaria durante 30 días y una mensual durante 12 meses, en `/var/backups/worldives`.

**Muy recomendable: una copia fuera del servidor.** Configura `rclone` con un almacenamiento en la UE y pon en el
`.env` `WOD_BACKUP_COMMAND=/opt/worldives/scripts/copia_externa.sh` (instrucciones dentro del script).

**Prueba de restauración (una vez al mes):**

```bash
sudo -u worldives .venv/bin/python app/server.py --verify-backup /var/backups/worldives/db/<copia>.sqlite3.gz
```

Restaurar de verdad: apartado 7 de `docs/despliegue/README.md`.

## 9. Actualizar sin perder datos

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

Comprueba la web y el *Estado del sistema*. Si algo va mal: `sudo systemctl stop worldives`, vuelve a poner
`/opt/worldives-anterior` en su sitio y arranca de nuevo.

## 10. Lista antes de abrir al público

- [ ] Dominio con HTTPS y redirección de `www`.
- [ ] Administrador creado, con la verificación en dos pasos activada.
- [ ] *Estado del sistema*: sin «Error»; los «Pendiente» son los que has decidido dejar para más tarde.
- [ ] Correo configurado y autenticado (SPF, DKIM y DMARC: `docs/despliegue/README.md`, apartado 10).
- [ ] Stripe en modo real (`sk_live_…`) y los dos webhooks.
- [ ] Copia fuera del servidor y una prueba de restauración hecha.
- [ ] Textos legales revisados por el abogado y datos del titular en *Administración → Legal*.
- [ ] Monitor externo contra `https://worldives.com/api/health`.
