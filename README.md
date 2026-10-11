# WORLDIVES DISCOVERY (v50.38)

Plataforma de descubrimiento y reservas de buceo: catálogo de puntos y centros con mapa, reservas y cobros
directos con Stripe Connect, ficha y Log Book del buceador, puntos, reseñas, panel de centros y profesionales
con planes, y administración completa. **Python 3.11+ con la biblioteca estándar, SQLite y HTML/CSS/JavaScript
sin compilar.** Dependencias mínimas: `stripe`, `qrcode` y `fonttools` (`requirements.txt`).

## Arranque local

```bash
pip install -r requirements.txt
./start_unix.sh          # o start_windows.bat
```

Abre `http://localhost:8000` (no abras `index.html` con doble clic). La primera vez se crea `data/worldivesdiscovery.sqlite3`
a partir del catálogo de demostración (`data/demo/catalogo-demo.sqlite3`). Crea el administrador con
`python app/server.py --create-admin`. La configuración va en `.env` (plantilla: `.env.example`); el servidor la lee solo.

## Roles

- **Visitante:** catálogo, mapa, fichas, «Solicitar información», denuncias.
- **Buceador:** reservas, ficha y documentos, Log Book, puntos y ventajas, reseñas, privacidad (descarga ZIP y baja).
- **Centro:** propietario, recepción o instructor, con planning, reservas, clientes, servicios, cobros, estadísticas,
  herramientas (CSV, iCal, widget, importación), equipo, datos fiscales y plan.
- **Profesional freelance sin centro:** como un centro, con su propia cuenta de cobros.
- **Administración** (con verificación en dos pasos obligatoria): catálogo, centros, verificaciones, pagos,
  denuncias, textos legales, planes, funciones, mapas, correos y operación.

## Documentación

| Tema | Dónde |
|---|---|
| Qué se ha hecho en cada versión, pendientes de decisión y temas para abogado y gestoría | `RELEASE_NOTES_v50_31.md` … `RELEASE_NOTES_v50_38.md` |
| Entrega final: estado, pruebas (también permisos entre roles), lanzamiento, abogado y gestoría | `docs/entrega/entrega-final.md` (tabla completa en `docs/entrega/estado.md`) |
| Despliegue en VPS, HTTPS, systemd, copias, restauración, monitorización, rendimiento, correo | `docs/despliegue.md` y `deploy/` |
| Mapas (Protomaps, satélite Esri, GEBCO) | `docs/mapas.md` |
| Estados de una reserva | `docs/estados-reserva.md` |
| Documentos legales, inventario, lista de lanzamiento y guías | `docs/legal/` |
| Seguridad | `SECURITY.md` |

## Base de datos

SQLite en modo WAL. El esquema completo está en el código (`BASE_SCHEMA` en `app/server.py`) y las migraciones se
aplican solas al arrancar: solo añaden y transforman, y antes de reescribir datos hacen una copia completa. La base de
producción **empieza limpia** con `tools/crear_base_produccion.py` (solo catálogo y textos legales). `data/*.sqlite3`
nunca se sube al repositorio.

## Pruebas

```bash
cd tests && python -m unittest discover -p 'test_*.py'      # pruebas de API y de cada fase (siempre sobre una copia)
python tests/e2e_centers.py                                  # pruebas en navegador (Playwright), una por fase
```

## Pagos con Stripe Connect (v50.34)

**WORLDIVES no cobra comisión por las reservas.** Su único ingreso es la cuota del plan anual de los centros. Los cobros online son **cargos directos**: el Checkout se crea en la cuenta de Stripe del centro (o del profesional freelance sin centro) con `stripe_account=…`, sin `application_fee_amount` ni `transfer_data`. El dinero va del buceador al prestador y nunca pasa por un saldo de WORLDIVES.

### Variables de servidor

Solo en el entorno del servidor (nunca en JavaScript, en el repositorio ni dentro del ZIP). Ver `.env.example`.

```text
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...           # endpoint de la plataforma
STRIPE_CONNECT_WEBHOOK_SECRET=whsec_...   # endpoint de Connect (eventos de las cuentas de los centros)
WOD_PUBLIC_URL=https://tu-dominio.example
# Configuración de las cuentas conectadas (valores por defecto = decisión del titular):
WOD_STRIPE_DASHBOARD=full        # panel completo de Stripe para el centro
WOD_STRIPE_FEES_PAYER=account    # las comisiones de Stripe las paga la cuenta del centro
WOD_STRIPE_LOSSES=stripe         # Stripe responde de los saldos negativos
WOD_STRIPE_CAPABILITIES=card_payments
```

### Alta de un centro o de un freelance

Desde **Cobros y pagos** en su panel. WORLDIVES crea una cuenta conectada con **propiedades de controlador** (Accounts v1: `controller.stripe_dashboard.type=full`, `controller.fees.payer=account`, `controller.losses.payments=stripe`, `requirement_collection=stripe`) y solo la capacidad `card_payments`, y abre el alta alojada por Stripe (Account Link). Se guardan solo el identificador de la cuenta y sus estados. No se puede cobrar online hasta que Stripe indique `charges_enabled` y `payouts_enabled`; `account.updated` los mantiene al día. Con el panel completo, el centro entra en `dashboard.stripe.com` con su propio usuario.

Las cuentas Express de prueba creadas con versiones anteriores no pueden cambiar de tipo: el administrador las desvincula (`POST /api/payments/connect/unlink`) y el centro conecta una nueva.

### Pago de una reserva

- «Pago al reservar»: Checkout al momento (total o **señal**), plazas bloqueadas 15 min, confirmación solo con el pago confirmado por Stripe.
- «Bajo petición»: Checkout cuando el centro acepta, con plazo para pagar.
- Señal: por servicio, porcentaje o importe por persona. La reserva guarda lo pagado (`amount_paid`) y lo pendiente (`amount_due`); el resto se registra con «Registrar cobro».

La reserva solo se considera pagada cuando Stripe lo confirma (webhook firmado, o consulta directa a Stripe al volver del pago). Los eventos se registran por ID para no procesarlos dos veces.

### Devoluciones

Las hace el centro desde su panel (botón «Devolver», total o parcial) con `Refund.create` en su cuenta, o desde su panel de Stripe; ambas llegan al historial `payment_refunds`. Un reembolso parcial no cancela la reserva. Si el buceador cancela una reserva pagada, se propone al centro el importe de su política y se le recuerda a las 72 h. El administrador solo ve pagos y devoluciones y marca incidencias.

### Webhooks

```text
POST https://tu-dominio.example/api/payments/webhook          (cuenta de la plataforma)
POST https://tu-dominio.example/api/payments/webhook/connect  (Connect: «eventos de las cuentas conectadas»)
```

Eventos: `checkout.session.completed`, `checkout.session.async_payment_succeeded`, `checkout.session.async_payment_failed`, `checkout.session.expired`, `payment_intent.payment_failed`, `charge.refunded`, `refund.created`, `refund.updated`, `charge.dispute.created`, `charge.dispute.closed`, `account.updated`, `account.application.deauthorized`. En el endpoint de Connect, un evento de una cuenta nunca puede tocar un pago de otra.

### Importante antes de producción

Antes de aceptar dinero real: HTTPS, secretos fuera del repositorio, copias de seguridad, términos y política de cancelación revisados por un abogado y configuración fiscal revisada por la gestoría (ver `docs/`).


## Seguridad y GitHub

La versión de distribución incluye `.gitignore` para evitar que secretos, configuraciones locales, almacenamiento privado y archivos WAL/SHM de SQLite terminen en GitHub. Usa `.env.example` como plantilla y define los secretos únicamente en el entorno donde se ejecuta el servidor.

Para uso local: `start_unix.sh` (Linux/macOS) o `start_windows.bat` (Windows). Para acceso desde otros dispositivos de la misma LAN, usa `start_windows_lan.bat` conscientemente.

Consulta `SECURITY.md` antes de publicar la aplicación.
