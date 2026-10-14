#!/usr/bin/env bash
# Cortafuegos del VPS de WORLDIVES (ASVS 5.0 V13.2.5), con ufw. Ejecutar como root, una vez y tras cada cambio:
#
#   sudo SSH_DESDE="203.0.113.10 198.51.100.0/24" SMTP_PUERTO=587 bash scripts/despliegue/cortafuegos.sh
#
#   SSH_DESDE    IPs o redes (separadas por espacios) desde las que se puede entrar por SSH. Recomendado: tu casa, tu
#                oficina o tu VPN. Vacío = SSH desde cualquier sitio, con límite de intentos (ufw limit).
#   SMTP_PUERTO  puerto de salida del correo (587 con STARTTLS o 465 con TLS). Por defecto 587.
#
# Entrada: solo 22 (SSH), 80 y 443 (web; 443/udp para HTTP/3 de Caddy).
# Salida: solo lo que necesitan los servicios de docs/legal/inventario.md §7.2:
#   53     DNS (resolver los nombres de todos los servicios)
#   123    NTP (hora exacta; los registros van en UTC)
#   67     DHCP (si el proveedor da la dirección del VPS por DHCP)
#   443    HTTPS: Stripe, Better Stack (registros), geocodificador, satélite (Esri), Meta/WhatsApp, Firebase,
#          plataformas de vídeo, destino de las copias (rclone), Let's Encrypt, firmas del antivirus (freshclam)
#          y actualizaciones de seguridad
#   80     HTTP: repositorios de Ubuntu (apt; los paquetes van firmados) y la validación de Let's Encrypt
#   587/465  correo (SMTP con TLS comprobado)
# ufw filtra por puerto y no por nombre: las direcciones de Stripe, Better Stack o Meta cambian sin aviso. Qué servicio
# usa cada puerto, y qué datos recibe, está en docs/legal/inventario.md §7.2. La web además solo se conecta a
# direcciones públicas (nunca a la red interna) y el servicio de systemd lo refuerza (IPAddressDeny en worldives.service).
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then echo "Ejecútalo con sudo." >&2; exit 1; fi
command -v ufw >/dev/null || apt-get install -y ufw
SMTP_PUERTO="${SMTP_PUERTO:-587}"
case "$SMTP_PUERTO" in 587|465) ;; *) echo "SMTP_PUERTO debe ser 587 o 465." >&2; exit 1 ;; esac

ufw --force reset >/dev/null
ufw default deny incoming
ufw default deny outgoing
ufw default deny routed

# --- Entrada
if [ -n "${SSH_DESDE:-}" ]; then
  for origen in $SSH_DESDE; do ufw allow in proto tcp from "$origen" to any port 22 comment 'SSH (IP conocida)'; done
else
  echo "Aviso: SSH abierto a cualquier IP (con límite de intentos). Mejor: SSH_DESDE=\"tu-ip\"." >&2
  ufw limit in 22/tcp comment 'SSH (limite de intentos)'
fi
ufw allow in 80/tcp comment 'web: http (redirige a https; /api da 403)'
ufw allow in 443/tcp comment 'web: https'
ufw allow in 443/udp comment 'web: https HTTP/3'

# --- Salida
ufw allow out 53 comment 'DNS'
ufw allow out 123/udp comment 'NTP (hora)'
ufw allow out 67/udp comment 'DHCP (si el VPS renueva su direccion)'
ufw allow out 443/tcp comment 'HTTPS: Stripe, Better Stack, Esri, Meta, Firebase, copias, LE, freshclam, apt'
ufw allow out 80/tcp comment 'HTTP: apt (paquetes firmados) y Lets Encrypt'
ufw allow out "$SMTP_PUERTO"/tcp comment 'correo (SMTP con TLS)'

ufw logging low
ufw --force enable
ufw status verbose
