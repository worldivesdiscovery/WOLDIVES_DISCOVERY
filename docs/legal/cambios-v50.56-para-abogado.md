# Cambios en los textos legales (v50.56) · para la revisión del abogado

Fecha: 15/10/2026. Motivo: el encargo del titular **«Motor de reservas multicanal + seguros de buceo»**. Los textos **no
se publican en el servidor real** hasta que el abogado los revise. Este documento tiene dos bloques: el motor de
reservas (Bloque 1) y los seguros de buceo (Bloque 2, más abajo).

## Bloque 1 · Motor de reservas multicanal

Desde la v50.56 un centro puede vender sus plazas en **su propia web** (widget), en **su página de reservas de
WORLDIVES** (`/c/<centro>`), con **enlaces y códigos QR**, por una **API** con sus claves y **a mano** desde el panel.
Todos los canales salen del mismo inventario.

### 1. Lo que ha cambiado

| Documento | Dónde | Qué cambia |
|---|---|---|
| **Política de privacidad** (9 idiomas) | `app/legal/<idioma>/privacidad.md`, final del §1 | Párrafo nuevo: quien reserva en la web, la página o un enlace de un centro sin entrar con su cuenta de WORLDIVES es **cliente del centro**; el centro es **responsable** y WORLDIVES **encargado** (art. 28 RGPD); sin publicidad de WORLDIVES; ningún otro centro lo ve; los derechos se ejercen ante el centro; si crea una cuenta, es una relación aparte con su propio consentimiento. Texto exacto en el punto 2. |
| **Anexo de encargo del tratamiento** (borrador interno, no publicado) | `docs/legal/anexo-encargado-tratamiento.md`, apartado **A.5** nuevo y cláusulas 1, 3, 4 y 5 | Las reservas por widget, página, enlace y API, los webhooks y el iCal como encargo del centro, con lo que hace el código y la prueba de cada regla. |
| Texto en el widget (9 idiomas), paso «Tus datos», con casilla obligatoria | `app/wod/widget_textos.py` (`processor`) | «Reservas con {centro}. WORLDIVES gestiona la reserva por encargo del centro.» |
| Pie del widget y de los correos de esas reservas (9 idiomas) | `app/wod/widget_textos.py` (`powered`), `app/emails/<idioma>.json` | «Reservas con tecnología de WORLDIVES» y «Recibes este correo por tu reserva con {centro}…». Los correos llevan el nombre, el logo y el color del centro, y las respuestas van al centro. |

Cómo se publican: como en versiones anteriores, el texto cambiado se convierte en una **versión nueva** de la política
de privacidad al instalar la v50.56 y se pide aceptarla al entrar. Si la administración ya editó la política en la web,
su versión manda y este párrafo hay que copiarlo a mano.

### 2. Texto exacto del párrafo nuevo (castellano)

> **Si reservas en la web, en la página de reservas o con un enlace de un centro** (verás «Reservas con tecnología de
> WORLDIVES») sin entrar con una cuenta de WORLDIVES, eres cliente de ese centro: **el centro es el responsable** de tus
> datos y WORLDIVES los trata **por su encargo** (art. 28 RGPD), solo para gestionar tu reserva, el pago y los correos
> sobre ella. No los usamos para nuestra publicidad y ningún otro centro los ve. Para ejercer tus derechos, dirígete al
> centro (puedes responder a cualquiera de sus correos); si nos escribes a nosotros, se lo trasladamos. Si además creas
> una cuenta de WORLDIVES, esa cuenta es una relación aparte con nosotros, con tu propio consentimiento, y la reserva
> sigue siendo del centro.

### 3. Comprobado con pruebas

- El cliente del widget queda como ficha del centro, sin cuenta, y no se enlaza a ninguna cuenta aunque el email coincida.
- Los correos comerciales de WORLDIVES lo excluyen, incluso con el permiso marcado por error.
- Ningún otro centro ve su reserva, su ficha ni su exportación.
- El widget no pone cookies ni guarda nada en el navegador, y no carga nada de terceros.
- Los correos llevan la marca del centro y la respuesta va al centro.

Pruebas: `tests/test_v50_56_widget.py` (`test_cliente_del_widget_es_del_centro`, `test_correo_con_la_marca_del_centro`,
`test_widget_js_ligero_y_sin_cookies`, `test_cabeceras_dominios_y_sin_cookies`) y `tests/test_v50_47_aislamiento.py`.

### 4. Preguntas para el abogado

1. **Calificación.** Centro responsable y WORLDIVES encargado en las reservas por widget, página, enlace y API. ¿Cambia
   algo si el cliente tiene cuenta de WORLDIVES pero reserva sin entrar?
2. **Información al cliente (art. 13).** ¿Bastan el texto del widget y el párrafo de la privacidad de WORLDIVES, o el
   centro debe enlazar **su propia** política en el widget? Se puede añadir un campo «Política de privacidad del centro»
   en «Vender en tu web».
3. **Cuenta opcional al final.** ¿Hace falta un aviso más («tu reserva seguirá siendo del centro»)? ¿Se puede ofrecer
   sin permiso previo del centro?
4. **Anexo de encargo.** ¿Se acepta en línea, con las condiciones para centros, o como documento aparte? Hoy no está
   publicado (ver la Parte A del anexo).
5. **Webhooks a servidores fuera de la UE.** Si el centro indica un servidor fuera de la UE, ¿es una transferencia del
   centro (responsable) por su instrucción y basta con la cláusula 6 del anexo?
6. **Seguridad del widget.** Para frenar abusos se cuenta en memoria cuántas reservas llegan desde la misma IP, y a
   partir de 5 en 10 minutos el navegador hace una comprobación invisible. La IP no se guarda. ¿Hace falta mencionarlo?

## Bloque 2 · Seguros de buceo

Desde la v50.56 el buceador guarda su póliza en **«Mi seguro de buceo»**, ve si está vigente y recibe avisos antes de
que caduque; cada servicio dice si exige seguro; el centro ve el estado del seguro de sus buceadores; y una ventana
**«Contrata tu seguro de buceo»** enlaza con **aseguradoras colaboradoras**.

**La regla que sigue el código** (Real Decreto-ley 3/2020): WORLDIVES **no es aseguradora ni mediador de seguros**. No
vende, no cobra, no recomienda ni compara coberturas: solo enlaza con la web de la aseguradora, donde se contrata y se
paga. **Ninguna aseguradora está escrita en el código**: se dan de alta en Administración → Seguros. Hoy no hay ninguna
real (solo las dos inventadas de la demo).

### 1. Lo que ha cambiado

| Documento | Dónde | Qué cambia |
|---|---|---|
| **Política de privacidad** (9 idiomas) | `app/legal/<idioma>/privacidad.md`: viñeta nueva tras «El centro o profesional con el que reservas» y fila nueva en la tabla de conservación | Qué ve el centro del seguro y cuándo; el documento solo si el buceador lo comparte; la póliza que sube un centro solo llega al perfil con su «sí»; registro de cada consulta; el enlace a la aseguradora no le envía datos; conservación de las pólizas. Texto exacto en el punto 2. |
| **Aviso junto a cada aseguradora** (9 idiomas, editable) | Administración → Seguros → Textos legales (valores por defecto en `app/wod/seguros.py`, `LEGAL_DEFAULTS`) | «La contratación se realiza en la web de [aseguradora]. WORLDIVES no es aseguradora ni mediador de seguros.» |
| **Marca «Colaborador»** (enlace con comisión) | ídem | «Colaborador: WORLDIVES puede recibir una compensación de [aseguradora] si contratas desde este enlace. No cambia el precio que pagas.» |
| **Marca «Destacado»** (prioridad pagada) | ídem | «Destacado: [aseguradora] paga para aparecer en primer lugar.» |
| **Correo y aviso en la app de caducidad** (9 idiomas) | `app/server.py`, plantilla `insurance_diver_expiring` | A 30, 7 y 1 días y el día que caduca, con «Renovar o contratar seguro» y la nota «WORLDIVES no es aseguradora ni mediador de seguros: la contratación se hace en la web de cada aseguradora…». |
| **Correo «[centro] ha añadido tu seguro»** (9 idiomas) | plantilla `insurance_policy_added` | Pide al buceador que decida si guarda en su perfil la póliza que subió el centro. |
| **Nota en la confirmación de la reserva** (9 idiomas) | `booking_mail_ctx`, `insurance_note` | Cuando el servicio pide seguro y no consta uno válido: «Recuerda llevar tu seguro de buceo vigente… Si no lo tienes, en WORLDIVES encontrarás enlaces a aseguradoras con seguro de día (se contrata en su web).» |

Cómo se publican: igual que en el Bloque 1, la política de privacidad cambiada pasa a ser una **versión nueva** al
instalar la v50.56. Los avisos de las aseguradoras se cambian en la web sin instalar nada.

### 2. Texto exacto de lo nuevo en la política de privacidad (castellano)

> **Tu seguro de buceo (v50.56):** el centro con el que reservas ve si tu seguro está vigente el día de la inmersión
> (estado, aseguradora, tipo y fechas, nunca el número de póliza), y solo desde que confirma la reserva hasta 7 días
> después; el documento, solo si activas «Compartir también el documento de la póliza». Si un centro sube una póliza
> para tu reserva, solo pasa a tu perfil si lo aceptas. Cada consulta queda registrada. Al pulsar «Contratar en …»
> abrimos la web de la aseguradora sin enviarle ningún dato tuyo: solo contamos el clic, sin saber quién lo hizo.
> WORLDIVES no es aseguradora ni mediador de seguros.

> Fila de conservación: **Pólizas de «Mi seguro de buceo»** · Hasta que las borres o elimines tu cuenta. Las caducadas
> se borran solas pasado el plazo configurado (12 meses por defecto), salvo que cubran una reserva en reclamación.

### 3. Cómo se cumple (lo que hace el código)

- **No vende ni cobra.** «Contratar en [aseguradora]» abre su web en otra pestaña (`/seguros/ir/<producto>` → 302 a la
  dirección que dio la aseguradora). Solo se admiten direcciones **https** de sus **dominios autorizados**; se añade
  únicamente su **código de colaborador**. Sin nombre, correo ni referencia de la página (`Referrer-Policy: no-referrer`).
- **No recomienda ni compara.** La ventana enseña por cada aseguradora: logo, nombre del producto, «desde X €», zona y el
  botón. No hay valoraciones ni coberturas comparadas. Orden **neutral** (alfabético o rotando cada día); solo
  aparece primero quien paga por ello, y entonces lleva la marca **«Destacado»**.
- **Transparencia.** Cada aseguradora lleva el aviso legal; las que pagan comisión, «Colaborador».
- **Datos personales.** Ninguno va a la aseguradora. El clic se cuenta agregado (mes, aseguradora, producto, país y si
  era para buceador o centro), sin persona. Preparada para el futuro una casilla «Rellenar su formulario con mis
  datos (solo si lo marco)»: hoy no sale porque ninguna aseguradora tiene conexión directa.
- **Conexión directa con aseguradoras (API):** preparada y **desactivada** (`WOD_INSURANCE_API`), con firma de cada
  aviso. No se activa sin acuerdo.
- **La póliza del buceador:** sin datos médicos (se rechazan), archivo comprobado por su contenido real (PDF, JPG o PNG,
  10 MB), fotos sin datos ocultos (EXIF, GPS), almacenamiento privado, número de póliza cifrado. La lectura del PDF solo
  **propone** fechas y número: no se guarda nada sin confirmar. El buceador la borra cuando quiere; se incluye en
  «Descargar mis datos» y se borra con la cuenta.
- **El centro** ve el estado (🟢🔴⚪), la aseguradora, el tipo y las fechas solo de **sus** buceadores, desde la
  confirmación hasta 7 días después; nunca el número; el documento solo si el buceador lo comparte o lo subió el centro.
  Cada vista y cada intento denegado quedan en el registro.

### 4. Comprobado con pruebas

`tests/test_v50_56_seguros.py` (13 pruebas): estados y avisos, archivos (PDF falso, 20 MB, EXIF, sin sesión), lectura del
PDF solo como propuesta, reserva «obligatorio» y «se comprueba en el centro», enlace con código y sin datos (dominio no
autorizado rechazado), visibilidad del centro (solo lo suyo, en su plazo, registrado), la póliza del centro necesita el
«sí», canales (WORLDIVES, widget, API), retención salvo disputa, textos legales en 9 idiomas, avisos y ventana en 9
idiomas, descarga de datos y borrado de cuenta. En navegador: `tests/navegador/e2e_v50_56_seguros.py` (52
comprobaciones).

### 5. Pendiente de decisión del abogado

1. **El papel de WORLDIVES en la distribución de seguros.** Con enlaces que pueden llevar comisión («Colaborador») y
   prioridad pagada («Destacado»), ¿la actividad entra en el Real Decreto-ley 3/2020 (por ejemplo, como auxiliar
   externo o colaborador de una aseguradora) y hace falta **inscripción en el registro de la DGSFP** o un contrato
   concreto con cada aseguradora? Si hiciera falta, ¿se puede seguir enlazando sin comisión mientras tanto?
2. **Los textos exactos** del aviso, de «Colaborador» y de «Destacado» en los 9 idiomas, y dónde deben verse (hoy:
   debajo de cada aseguradora, en la ventana y en el widget).
3. **«Desde X €».** ¿Mostrar el precio de partida que da la aseguradora puede entenderse como comparar? Se puede quitar
   de la ventana sin tocar nada más.
4. **El texto de la confirmación de la reserva** («en WORLDIVES encontrarás enlaces a aseguradoras con seguro de día»)
   y el botón «Renovar o contratar seguro» de los avisos de caducidad: ¿son adecuados?
5. **Póliza que sube el centro** para un cliente **sin cuenta** (widget, reserva manual): se guarda solo en esa
   reserva. ¿Basta con la base de la reserva (ejecución del contrato) y el encargo del centro?
6. **Plazo del centro** (desde la confirmación hasta 7 días después) y **conservación** (12 meses tras caducar, salvo
   reclamación): ¿son proporcionados?
7. **La casilla futura** «Rellenar su formulario con mis datos»: texto del consentimiento y qué datos podrían enviarse.

