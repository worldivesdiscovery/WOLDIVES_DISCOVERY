# Cambios en los textos legales (v50.55) · para la revisión del abogado

Fecha: 15/10/2026. Motivo: dos encargos del titular, **«Pago en persona» para freelance** y **«Seguridad de la app
WORLDIVES PRO»**. Los textos **no se publican en el servidor real** hasta que el abogado los revise. Lo marcado
**[PENDIENTE ABOGADO]** en el encargo está aquí con el texto exacto que hoy se enseña.

## 1. Lo que ha cambiado

| Documento | Dónde | Qué cambia |
|---|---|---|
| **Pago en persona al profesional** (documento nuevo, 9 idiomas) | `app/legal/<idioma>/pago-en-persona.md` · `#/legal/pago-en-persona` | Reglas del cobro directo del freelance: solo «Bajo petición», precio obligatorio y público, WhatsApp visible solo tras aceptar, el profesional es el único responsable de cobros, impuestos, Seguridad Social, seguro, cancelaciones y devoluciones; WORLDIVES no cobra ni media. El freelance lo acepta con una casilla la primera vez que activa «Pago en persona» (queda registrada la versión y la fecha, como las demás aceptaciones). |
| **Condiciones para centros y profesionales** (9 idiomas) | `app/legal/<idioma>/centros.md`, párrafo antes del §7 | Párrafo nuevo «Pago en persona (profesionales independientes)» que remite al documento anterior. |
| **Condiciones de reserva** (9 idiomas) | `app/legal/<idioma>/reservas.md`, párrafo antes del §4 | Párrafo nuevo «Pago en persona al profesional»: el cliente envía una solicitud, el precio es el publicado, acuerda el pago por WhatsApp; WORLDIVES no cobra, no devuelve y no gestiona cancelaciones ni incidencias en esos servicios. |
| **Política de privacidad** (9 idiomas) | `app/legal/<idioma>/privacidad.md` §2 y §5 | §2 «Datos técnicos»: en la app, modelo y sistema del móvil, versión de la app y ciudad aproximada de cada inicio de sesión («Dispositivos conectados» y aviso de dispositivo nuevo); la huella, la cara y el PIN los comprueba el móvil y **nunca llegan** al servidor. §2 «Centros y profesionales»: el WhatsApp de contacto del profesional que cobra en persona (cifrado), visible para el cliente cuando acepta. §5 «Sesiones»: web 8 h sin actividad; app 15 minutos renovables y como mucho 30 días por dispositivo; dispositivos sin usar 13 meses, olvidados. |
| Correo nuevo **«Nuevo inicio de sesión»** (9 idiomas) | plantilla `new_device_login` en `app/server.py` | Aviso de seguridad (no comercial) al entrar desde un dispositivo que la cuenta no conocía. No se envía en el primer dispositivo de cada cuenta. |
| Aviso del pago en persona en la reserva, los correos y el PDF | `app/wod/presencial.py` (`NOTICE`) | Ver el texto exacto en el punto 2. |

Cómo se publican: como en versiones anteriores, cada texto cambiado se convierte en una **versión nueva** del
documento al instalar la v50.55 y se pide aceptarla al entrar (las condiciones para centros, con 15 días de preaviso).
Si la administración ya editó un documento en la web, su versión manda y estos cambios hay que copiarlos a mano.

## 2. Textos exactos marcados [PENDIENTE ABOGADO]

**Aviso al cliente** (ficha del servicio, hoja de reserva de la app, reserva, correos y justificante PDF), con una
casilla obligatoria antes de «Enviar solicitud»:

> Este profesional cobra directamente, no a través de WORLDIVES. El precio es el publicado aquí. Acuerda con él la
> forma de pago y los detalles por WhatsApp. En este servicio WORLDIVES no gestiona pagos, devoluciones,
> cancelaciones ni incidencias.

Casilla: «He leído el aviso: pago en persona al profesional». Queda guardado en la reserva cuándo se marcó
(`in_person_ack_at`) con la versión del aviso (`NOTICE_VERSION = 2026-10-15`).

**Si el profesional no publica política de cancelación**:

> Este profesional no ha publicado una política de cancelación. WORLDIVES no gestiona cancelaciones ni devoluciones en
> este servicio.

**Al cancelar el cliente**:

> Si cancelas, se libera tu plaza y avisamos al profesional. WORLDIVES no gestiona pagos ni devoluciones en este
> servicio: si le has pagado algo, resuélvelo directamente con él.

## 3. Preguntas para el abogado

### Pago en persona

1. **Papel de WORLDIVES.** En estos servicios la web solo publica la oferta, recoge la solicitud y, al aceptar, enseña
   el WhatsApp del profesional. ¿Basta el aviso y la cláusula para que quede claro que WORLDIVES es un intermediario
   (prestador de servicios de alojamiento de datos, Reglamento (UE) 2022/2065) y no parte del contrato ni del cobro?
2. **Información al consumidor en un mercado en línea** (art. 6 bis de la Directiva 2011/83/UE, introducido por la
   Directiva (UE) 2019/2161, y su transposición en el TRLGDCU): ¿hay que decir en la ficha si el profesional es
   empresario o no y que los derechos de consumidor no se aplican frente a WORLDIVES? Hoy la ficha dice quién presta
   el servicio y el aviso anterior; no dice «empresario / no empresario».
3. **Desistimiento.** Las actividades de ocio con fecha concreta están exceptuadas del derecho de desistimiento
   (art. 103 l) TRLGDCU). ¿Hay que decirlo expresamente en el aviso o basta la política del profesional?
4. **Política de cancelación libre.** El profesional escribe su propia política (máx. 1000 caracteres) o ninguna. ¿Hace
   falta un mínimo (por ejemplo, que no pueda contradecir la ley de consumo) o un aviso de que es responsabilidad suya?
5. **WhatsApp del profesional.** Se guarda cifrado y solo lo ve el cliente con una reserva aceptada. ¿Es suficiente
   la aceptación del freelance (casilla con el documento) como base para mostrarlo, o hace falta un consentimiento
   aparte? ¿Algo que añadir sobre el uso de WhatsApp (Meta) como canal elegido por las partes?
6. **Incidencias y reseñas.** Si un cliente denuncia que el profesional no se presentó o cobró otro precio, la web
   solo ofrece la vía de denuncias de contenidos y las reseñas. ¿Hay que decir algo más (resolución de litigios en
   línea, hojas de reclamaciones)?
7. **«Cobrado» y «No se presentó».** El profesional marca cada reserva para su control; el cliente no lo ve y no
   cambia nada. ¿Algún riesgo en guardar esa marca (dato del cliente, «no se presentó»)? Se borra con la reserva.

### Seguridad de la app

8. **Datos del dispositivo.** Modelo, sistema, versión de la app, IP en forma de huella y ciudad aproximada (solo si
   el proxy la envía) de cada sesión, para «Dispositivos conectados» y el correo de dispositivo nuevo. Base propuesta:
   interés legítimo (seguridad, art. 6.1.f y art. 32 RGPD). ¿De acuerdo? ¿Basta lo añadido en la política?
9. **Huella y cara.** La app usa el sistema del móvil (BiometricPrompt de Android); la plantilla biométrica nunca
   sale del móvil y la app solo recibe «sí» o «no». Entendemos que WORLDIVES **no trata datos biométricos** (art. 9
   RGPD). ¿Confirmado? ¿Conviene decirlo así en la política (hoy: «la huella, la cara y el PIN los comprueba tu móvil
   y nunca nos llegan»)?
10. **Correo «Nuevo inicio de sesión».** Es un aviso de seguridad del servicio, no comercial; se envía aunque la
    persona no acepte comunicaciones comerciales. ¿Correcto?
11. **El titular del centro cierra las sesiones de su equipo** (ve el dispositivo, el sistema y la última actividad de
    cada persona del equipo, no su ubicación). ¿Hay que informarlo en las condiciones de centros o en el anexo de
    encargado?

## 4. Qué cambia cuando el abogado responda

- Textos: se editan en `app/legal/<idioma>/` (o en *Administración → Legal*) y se vuelven a traducir los párrafos
  cambiados (la prueba `test_phase8_languages` avisa si falta alguno).
- Aviso del pago en persona: `app/wod/presencial.py` (`NOTICE`, `NOTICE_VERSION`) y sus traducciones
  (`scripts/idiomas/datos/v50_55_presencial.py`). Cambiar `NOTICE_VERSION` deja constancia de qué versión vio cada
  cliente.
- Correo de dispositivo nuevo: plantilla `new_device_login` y `scripts/idiomas/datos/v50_55_seguridad.py`.
