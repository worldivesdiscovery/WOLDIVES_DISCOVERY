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

(Se completa con la parte de seguros de esta misma versión.)
