WORLDIVES DISCOVERY — Encargo: motor de reservas multicanal + seguros de buceo
Dos bloques en un solo encargo. Hazlos en este orden: el Bloque 2 usa la función de reserva única del Bloque 1.
Bloque 1: motor de reservas multicanal (la web del centro y WORLDIVES, un solo calendario).
Bloque 2: seguros de buceo (control de vigencia y contratación rápida para buceadores y centros).
Pega este documento entero en la sesión de código.
Versión base: la última disponible.
Antes de cada punto: comprueba si ya está hecho y márcalo «Ya estaba», «Completado», «Nuevo» o «Pendiente de decisión». No rehagas lo que ya funciona: verifícalo con pruebas.
Encargos en los que se apoya (no se repiten aquí):
los dos modos de reserva (Fase 1B);
pagos y devoluciones (Fase 2);
el motor de agenda común (A1);
el widget y el enlace directo (Fase 6, punto 5);
el aislamiento entre centros.
Si algo de esos encargos falta o falla, se arregla aquí.
Prioridad máxima. Es el corazón del producto: WORLDIVES es un motor de reservas, no solo un escaparate.
BLOQUE 1 — Motor de reservas multicanal
Objetivo
Un centro de buceo (o un freelance) tiene que poder vender sus salidas, cursos y servicios desde su propia página web, con su marca, igual que hacen FareHarbor, Bókun o Checkfront. Esas reservas deben entrar en el mismo calendario y las mismas plazas que las que llegan por WORLDIVES.
Regla de oro: un solo inventario. Da igual por dónde entre una reserva:
el buscador de WORLDIVES;
la web del centro;
el enlace directo de Instagram o WhatsApp;
la API;
la reserva que el centro apunta a mano por teléfono o en el mostrador.
Todas descuentan plazas del mismo sitio, al momento. Una plaza vendida en un canal desaparece en todos. Nunca puede venderse una plaza dos veces.
Parte A — Revisión del estado actual (sin cambiar nada)
Entregar docs/reservas/multicanal-estado-actual.md con:
Canales que existen hoy y cómo funcionan: widget, enlace directo, reserva manual en el panel, API y feed iCal. Para cada uno, si escribe en las mismas tablas de plazas y reservas que el buscador de WORLDIVES o si va por otro camino.
Cómo se calculan y bloquean las plazas:
dónde se descuentan;
si hay bloqueo temporal mientras se paga;
qué pasa si dos personas reservan la última plaza a la vez desde dos canales distintos.
Prueba real de sobreventa: lanzar 20 reservas simultáneas a una salida con 3 plazas libres, mezclando canales. Anotar cuántas se confirman. Debe ser exactamente 3.
Lista de fallos con archivo, línea y gravedad.
Parte B — Inventario único y reglas de la reserva (el núcleo)
Una sola función de reserva en el servidor para todos los canales, por ejemplo create_booking(ctx, channel, …).
Ningún canal escribe reservas ni plazas por su cuenta.
Una prueba automática falla si alguien inserta reservas fuera de esa función.
Plazas a prueba de choques:
la comprobación y el descuento de plazas van en una transacción con bloqueo, para que dos reservas simultáneas nunca vendan la misma plaza;
lo mismo vale para la agenda común (instructores, barcos y días de freelance): nunca dos bloques solapados.
Bloqueo temporal mientras se paga («Pago al reservar»):
las plazas quedan apartadas un tiempo configurable (por defecto 10 minutos);
si el pago no se completa, se liberan solas;
el contador de plazas libres que ve el público las descuenta mientras tanto.
«Bajo petición»:
la solicitud no descuenta plazas hasta que el centro la acepta;
si al aceptar ya no quedan plazas, el centro no puede aceptarla y ve el motivo.
Cancelaciones, cambios de fecha y caducidades: liberan o mueven las plazas al momento, en todos los canales.
Reintentos sin duplicados: cada intento de reserva lleva una clave de idempotencia. Si el navegador o la red repiten la petición, nunca se crean dos reservas ni dos cobros.
Origen de cada reserva: se guarda el canal en un campo channel:
worldives (buscador y mapa);
widget (web del centro);
link (enlace directo, Instagram o WhatsApp);
api;
manual (teléfono o mostrador);
import.
Además se guarda el dominio de origen en el caso del widget. El centro lo ve en cada reserva y en sus informes: «Reservas por canal».
Zona horaria: todas las horas se guardan con la zona horaria del lugar del servicio. El widget, la API, los correos y el panel muestran siempre la hora local del centro.
Precio y moneda:
el precio sale siempre del servidor;
el navegador o la API nunca pueden mandar el precio;
precio por persona × participantes, extras y descuentos calculados igual en todos los canales.
Parte C — Canal 1: widget para la web del centro (el principal)
Código para pegar. El centro va a Panel → Vender en tu web y copia un fragmento de código de una o dos líneas para pegar en su web (WordPress, Wix, Squarespace, Webflow o HTML propio).
Tres formatos:
botón «Reservar» que abre la reserva en una ventana encima de su web;
calendario incrustado dentro de su página;
lista de salidas o servicios con sus próximas fechas y plazas.
Se puede filtrar por servicio, por tipo (bautizo, curso, inmersión…) o mostrar todo el catálogo del centro.
Con la imagen del centro:
su logo y su color principal, elegibles en el panel;
idioma automático según el navegador o fijado por el centro (9 idiomas);
moneda del centro.
WORLDIVES solo aparece en un pie discreto: «Reservas con tecnología de WORLDIVES».
El cliente reserva sin salir de la web del centro:
elige fecha, plazas y participantes;
rellena sus datos;
acepta la política de cancelación del centro;
paga con Stripe en la cuenta del centro o envía la solicitud («Bajo petición»).
No se le obliga a crear una cuenta de WORLDIVES. Puede reservar como invitado y, si quiere, crearse la cuenta al final para su Log Book.
Responsive: funciona en móvil y ordenador, y la altura del calendario incrustado se ajusta sola, sin barras de desplazamiento dobles.
Rápido y ligero:
el script del widget pesa menos de 50 KB;
se carga sin bloquear la web del centro;
no rompe los estilos de su página: se aísla dentro de un iframe o de Shadow DOM.
Seguridad del widget:
el centro indica en su panel los dominios autorizados (por ejemplo www.buceomarazul.com);
el widget solo funciona en esos dominios. El servidor lo controla con frame-ancestors en la cabecera CSP de cada centro, más la comprobación del origen;
protección contra bots: límite de intentos y verificación invisible si hay abuso.
Cookies y privacidad:
el widget no instala cookies de publicidad ni de seguimiento;
para que el centro mida sus ventas con sus propias herramientas, el widget envía eventos a la página que lo contiene («reserva iniciada», «reserva completada»). Es el centro quien decide si los usa, según su propio banner de cookies.
Correos y justificantes: las reservas del widget llevan el nombre y el logo del centro como protagonista. Los envía WORLDIVES con «responder a» el correo del centro.
Plan del centro:
el widget está incluido en el plan «Motor de reservas» y en «Pro»;
con la ficha gratuita, el widget muestra «Solicitar información» en lugar de reservar;
si el plan caduca, las reservas ya hechas se mantienen y se atienden con normalidad.
Parte D — Canal 2: enlace directo y página de reservas del centro
Página de reservas propia del centro en WORLDIVES, por ejemplo worldives.com/c/mar-azul, con el mismo motor que el widget. Sirve para centros sin web propia o para poner en Instagram, Google Maps y WhatsApp.
Enlaces directos a un servicio o a una fecha concreta, para compartir: «reserva el bautizo del sábado».
Código QR de cada enlace, descargable para imprimir en el mostrador o en el barco.
Parte E — Canal 3: API para centros con web a medida
API REST con versión (/api/v1/…) y documentación en docs/api/ con ejemplos.
Claves de API por centro:
se crean y revocan en el panel;
se guardan cifradas (en hash) y se muestran una sola vez;
tienen permisos de solo lectura (consultar disponibilidad) o lectura y escritura (crear reservas);
cada clave solo ve los datos de su centro, siguiendo las reglas del encargo de aislamiento.
Qué permite:
consultar servicios;
consultar disponibilidad y plazas en tiempo real;
crear una reserva o solicitud (por la misma función de la Parte B);
consultar y cancelar reservas.
Avisos automáticos (webhooks) a la dirección que el centro indique cuando una reserva se crea, se confirma, se paga, se cancela o cambia:
firmados (HMAC con secreto por centro);
con reintentos;
con un registro de entregas visible en el panel.
Límites de uso por clave y respuestas de error claras.
Parte F — Canal 4: reservas manuales del centro (teléfono, mostrador, agencia)
En el planning del centro, «Nueva reserva» en un toque:
cliente con nombre y teléfono o correo;
servicio, fecha y participantes;
estado del pago: pagado en el centro, pendiente o pagado online con enlace de pago.
Descuenta plazas igual que cualquier otra.
Bloqueos de plazas sin cliente: grupo, agencia o reserva de un hotel, con un texto libre.
Enlace de pago: el centro puede mandar al cliente un enlace para que pague online una reserva hecha por teléfono.
Parte G — Canal 5: calendarios externos
Exportar: el feed iCal privado por centro, por instructor y por freelance se mantiene (Fase 6). Comprobar que refleja cada reserva de cualquier canal en menos de 5 minutos.
Importar (bloqueos): el centro puede pegar la dirección iCal de otro sistema donde también vende, por ejemplo otra plataforma o su Google Calendar.
Los eventos importados bloquean plazas, recursos o días en WORLDIVES.
Se sincroniza cada 15 minutos.
En el panel queda claro que iCal no es instantáneo y que puede haber un desfase.
Conexión directa con otras plataformas (gestores de canales): queda pendiente de decisión del titular. Solo se documenta qué haría falta.
Parte H — Lo que ve el centro
Un único planning con todas las reservas de todos los canales:
cada una con una etiqueta de canal (WORLDIVES, web, enlace, API, manual);
filtro por canal;
en tiempo real, sin recargar la página.
Aviso de cada reserva nueva al momento, por correo y en el panel, venga por donde venga.
Informe «Ventas por canal»: número de reservas e importe por canal y por mes.
Pantalla «Vender en tu web» con:
el código para copiar y vista previa en vivo de cómo quedará;
los dominios autorizados;
las claves de API y los webhooks;
una guía paso a paso con capturas para WordPress, Wix y Squarespace.
Parte I — Datos personales de las reservas que entran por la web del centro
Los clientes que reservan desde la web del centro son clientes del centro. WORLDIVES:
los trata solo para gestionar la reserva, como encargado del tratamiento del centro;
no los usa para su propio marketing;
no los muestra a otros centros.
Si el cliente decide crearse una cuenta de WORLDIVES al final de la reserva, a partir de ahí es también usuario de WORLDIVES, con su propio consentimiento.
Preparar el texto para el abogado: contrato de encargo de tratamiento entre WORLDIVES y cada centro para estas reservas, aceptado en las condiciones para centros. Queda pendiente de revisión legal.
Pruebas obligatorias del Bloque 1 (sin ellas no se entrega)
Sobreventa:
20 reservas simultáneas por 4 canales distintos a una salida con 3 plazas: exactamente 3 confirmadas y 17 rechazadas con «Sin plazas»;
lo mismo con los días de un freelance y con un instructor en un curso de 3 días.
Bloqueo durante el pago:
mientras alguien paga en el widget, esas plazas no aparecen libres en WORLDIVES;
si abandona, a los 10 minutos vuelven a estar libres en todos los canales.
Cancelación cruzada: se reserva por el widget, se cancela desde el panel del centro y la plaza vuelve a verse libre en WORLDIVES y en el widget al momento.
Idempotencia: repetir la misma petición de reserva 5 veces da una sola reserva y un solo cobro.
Widget:
funciona pegado en una página de prueba;
no funciona en un dominio no autorizado;
no rompe los estilos de la página que lo contiene;
funciona en móvil, en los 9 idiomas y en los dos modos de reserva.
API y webhooks:
una clave de un centro no ve nada de otro;
una clave de solo lectura no puede crear reservas;
los webhooks llegan firmados y se reintentan si fallan;
una firma falsa se rechaza.
Pago: las reservas del widget y de la API cobran en la cuenta de Stripe del centro y nunca en la de otro. La devolución vuelve al mismo sitio.
Zona horaria: un centro en México y otro en España muestran sus horas locales correctas en el widget, los correos, el planning y el iCal.
iCal:
una reserva de cualquier canal aparece en el feed;
un evento importado bloquea la plaza en WORLDIVES.
Rendimiento:
el widget carga en menos de 2 segundos en un móvil 4G de gama media;
la disponibilidad responde en menos de 300 ms;
una reserva completa se hace en menos de 30 segundos.
Capturas:
el widget en una web de ejemplo, en móvil y ordenador;
el planning con reservas de varios canales;
la pantalla «Vender en tu web»;
el informe por canal.
Para que el titular lo pruebe
En el zip de pruebas:
una página web-de-centro-ejemplo.html (una web de centro de buceo inventada) con el widget de centro.prueba ya pegado en sus tres formatos;
una entrada nueva en README-PRUEBAS.md, «Probar el motor multicanal», con estos pasos:
reservar en la web de ejemplo;
ver que aparece en el panel del centro y que la plaza baja en WORLDIVES;
reservar la última plaza desde WORLDIVES;
ver que el widget ya dice «Completo»;
cancelar y ver que vuelve a haber plaza en los dos sitios.
BLOQUE 2 — Seguros de buceo: control de vigencia y contratación rápida
Objetivo
Para bucear hace falta un seguro de buceo vigente. Si un buceador no lo tiene o se le ha caducado, WORLDIVES debe:
detectarlo a tiempo;
ofrecerle contratarlo en un toque: seguro de día, de semana o de año, con las aseguradoras colaboradoras;
dejarlo subido a su perfil cuando lo tenga, para que el centro lo vea en la reserva.
Lo mismo para los centros: si un buceador llega al centro con el seguro caducado, el centro tiene que poder darle de alta un seguro desde su panel, en el momento.
Aseguradoras: el titular está negociando con varias (por ejemplo DAN Europe, AXA y otras especializadas en buceo). Por eso ninguna va escrita en el código: todas se configuran desde Administración.
Regla legal (importante; leer antes de programar)
WORLDIVES no es aseguradora ni mediador de seguros. Vender seguros en España es una actividad regulada (distribución de seguros, Real Decreto-ley 3/2020). Por eso, en esta primera versión:
WORLDIVES no vende, no cobra, no recomienda ni compara coberturas. Solo informa de que existen aseguradoras colaboradoras y lleva al buceador o al centro a la web de la aseguradora, donde se contrata y se paga.
Cada aseguradora aparece con su nombre y el texto: «La contratación se realiza en la web de [aseguradora]. WORLDIVES no es aseguradora ni mediador de seguros.»
Si WORLDIVES cobra por cada seguro contratado (enlace de afiliado o colaboración), el enlace se marca como «Colaborador» y se dice en las condiciones.
Pendiente de decisión del abogado:
si con el acuerdo de cada aseguradora WORLDIVES necesita inscribirse como colaborador o auxiliar en el registro de la DGSFP (Dirección General de Seguros);
los textos exactos que deben aparecer.
Dejarlo preparado como textos editables desde Administración.
Parte A — Revisión de lo que hay (sin cambiar nada)
Documentar en docs/seguros/estado-actual.md:
cómo se suben hoy los documentos del buceador y del centro (titulación, seguro, seguro de RC del centro);
dónde se guardan y quién puede verlos;
si hay fechas de caducidad y avisos.
Parte B — El seguro en el perfil del buceador
Apartado «Mi seguro de buceo» en «Mis documentos», con estos campos:
aseguradora;
número de póliza;
tipo (día, semana, año u otro);
válido desde y hasta;
zona cubierta (España, Europa, mundo);
profundidad máxima cubierta si la indica;
el archivo, en PDF, JPG o PNG.
Estado bien visible:
🟢 Vigente;
🟠 Caduca pronto (menos de 30 días);
🔴 Caducado;
⚪ Sin seguro.
Avisos automáticos por correo y en la app a 30, 7 y 1 días de que caduque, y el día en que caduca. Cada aviso lleva el botón «Renovar o contratar seguro».
Subida segura del archivo:
máximo 10 MB;
se comprueba el contenido real del archivo, no solo la extensión;
se borran los datos ocultos de las fotos (EXIF);
se guarda en almacenamiento privado: nunca con una dirección pública, solo servido por el servidor con permiso.
Lectura automática opcional: si el PDF trae texto, proponer la fecha de caducidad y el número de póliza leídos del documento, para que el buceador solo los confirme. Nunca se guarda sin su confirmación.
Sin datos médicos. El seguro no es un dato de salud y no se piden informes médicos (decisión ya tomada).
Borrado: el buceador puede borrar su documento cuando quiera. Los seguros caducados se borran automáticamente pasado un plazo configurable (por defecto 12 meses), salvo que haya una reserva en disputa.
Parte C — «Contratar seguro» para el buceador (botón de acceso rápido)
Dónde aparece:
en «Mi seguro de buceo», cuando está caducado, a punto de caducar o no hay seguro;
en la reserva, si la salida exige seguro (Parte E) y el del buceador no cubre esa fecha;
en los correos de aviso de caducidad;
en la confirmación de la reserva, si falta el seguro.
Qué ve: una ventana «Contrata tu seguro de buceo» con:
pestañas Día · Semana · Año;
en cada una, las aseguradoras colaboradoras que tengan ese producto para su país y el país de la inmersión, con su logo, el nombre del producto, «desde X €» si la aseguradora lo permite, la zona que cubre y el botón «Contratar en [aseguradora]»;
el aviso legal de la regla anterior.
Al pulsar: se abre la web de la aseguradora en una pestaña nueva, con el código de colaborador de WORLDIVES.
No se envía ningún dato personal del buceador a la aseguradora sin su consentimiento expreso.
Si en el futuro la aseguradora permite rellenar sus datos automáticamente, se pide permiso antes con una casilla: «Enviar mi nombre, correo y fechas a [aseguradora] para rellenar el formulario».
A la vuelta: al volver a WORLDIVES, el buceador ve «¿Ya lo tienes? Sube tu póliza», que lo lleva directamente a la subida de la Parte B con el tipo y la aseguradora ya rellenos.
Preparado para conexión directa (más adelante): si una aseguradora ofrece conexión directa (API), el seguro contratado podría llegar solo al perfil, con aviso firmado y sin que el buceador suba nada. Se programa la estructura (Parte G), pero queda desactivado hasta que haya acuerdo.
Parte D — Seguros desde el panel del centro
El caso real: llega un buceador al centro, su seguro está caducado y quiere bucear hoy. El centro abre la reserva (o el planning) y ve el estado del seguro de cada participante para la fecha de la salida: 🟢, 🔴 o ⚪.
Botón «Dar de alta seguro» junto al participante. Abre las aseguradoras colaboradoras para centros:
si la aseguradora tiene un programa para centros (el centro como colaborador suyo), se usa el enlace de ese programa;
si no, el enlace normal;
por defecto se muestra el seguro de día.
El centro lo contrata con el buceador delante, en la web de la aseguradora.
Subir la póliza: el centro puede subir la póliza contratada al perfil del buceador para esa reserva, solo si el buceador lo acepta. Le llega un aviso: «Mar Azul ha añadido tu seguro de día del 14/11. ¿Lo guardas en tu perfil?». Si no acepta, la póliza queda solo en esa reserva y se borra cuando termina el plazo de conservación.
Lo que puede ver el centro (privacidad):
solo el estado del seguro, la aseguradora, el tipo y las fechas de los buceadores con reserva en su centro, desde la confirmación hasta 7 días después de la inmersión;
el documento completo, solo si el buceador ha marcado «Compartir mi póliza con los centros donde reserve»;
cada vista del documento queda registrada.
Seguro de responsabilidad civil del propio centro (ya está en la Fase 6: subida, caducidad y avisos):
añadir junto a él el botón «Contratar o renovar seguro de RC del centro», con las aseguradoras colaboradoras para empresas de buceo;
mismo aviso legal.
Parte E — El seguro en la reserva
Ajuste por servicio que decide el centro: «Exige seguro de buceo», con tres opciones:
No;
Sí, se comprueba en el centro (valor por defecto);
Sí, obligatorio para reservar online.
Si lo exige y el buceador no tiene un seguro que cubra esa fecha:
con «se comprueba en el centro»: se avisa, se ofrece «Contratar seguro del día» y se deja reservar igualmente. En el justificante aparece «Recuerda llevar tu seguro de buceo vigente»;
con «obligatorio»: no puede confirmar hasta subir un seguro válido para la fecha, con el atajo para contratarlo y subirlo sin perder la reserva. Las plazas siguen bloqueadas mientras tanto, según la Parte B del bloque 1.
Funciona igual en todos los canales del Bloque 1: WORLDIVES, widget en la web del centro, enlace directo y API. En la API, el estado del seguro se devuelve como un campo.
Reservas con varios participantes:
cada participante con cuenta gestiona su propio seguro;
para los que no tienen cuenta, quien reserva puede indicar la aseguradora y la fecha de caducidad, o dejar «lo presentaré en el centro».
Parte F — Administración de aseguradoras
Administración → Seguros → Aseguradoras colaboradoras. Por cada aseguradora:
nombre, logo y web;
productos: tipo (día, semana, año, RC para centros), nombre, «desde X €» (opcional), zonas que cubre, países donde se vende e idiomas;
enlace de contratación para buceadores y para centros, con su código de colaborador. Solo se admiten direcciones https de los dominios autorizados para esa aseguradora;
etiqueta «Colaborador» si hay comisión;
orden de aparición, activo o inactivo, y fechas de inicio y fin del acuerdo.
Textos legales editables en los 9 idiomas: aviso de que WORLDIVES no es aseguradora y texto de colaborador.
Estadísticas agregadas, sin datos personales, para cuadrar comisiones con cada aseguradora:
clics por aseguradora, producto, país y mes;
pólizas subidas después de un clic.
Orden neutral: si no hay un acuerdo de prioridad, el orden se rota o es alfabético. Si una aseguradora paga por salir primero, se marca como «Destacado» (lo exige la normativa de transparencia de plataformas).
Parte G — Diseño escalable (preparado para crecer)
Una capa de proveedores (InsuranceProvider) con dos modos:
«enlace»: el que se usa ahora;
«API»: futuro, para consultar precio, contratar y recibir la póliza emitida por un aviso automático firmado que la adjunta sola al perfil.
Añadir una aseguradora nueva no requiere tocar el código, solo configurarla.
Modelo de datos:
insurance_providers;
insurance_products;
insurance_policies (del buceador o de una reserva, con su archivo privado);
insurance_clicks (agregados, sin datos personales).
Todo con las reglas de aislamiento entre centros.
Fechas y zonas horarias: la comprobación de «cubre esta fecha» usa la fecha local del lugar de la inmersión.
Pruebas obligatorias del Bloque 2
Estados:
un seguro vigente da 🟢;
uno que caduca en 10 días da 🟠 y se envía el aviso;
uno caducado da 🔴;
sin seguro, ⚪.
Reserva:
servicio con «obligatorio» y seguro caducado: no confirma hasta subir uno válido y no se pierden las plazas;
con «se comprueba en el centro»: deja reservar y avisa.
Contratar:
el botón abre la web correcta de la aseguradora, con el código de colaborador, en una pestaña nueva;
no se envía ningún dato personal sin consentimiento;
una dirección fuera de los dominios autorizados no se puede guardar.
Centro:
ve el estado del seguro solo de sus buceadores y solo en el plazo permitido;
no ve el documento si el buceador no lo comparte;
la póliza que sube el centro no llega al perfil sin el «sí» del buceador.
Archivos:
un archivo falso con extensión .pdf se rechaza;
uno de 20 MB se rechaza;
el documento no se puede abrir con su dirección sin haber iniciado sesión con permiso.
Canales: el control del seguro funciona igual por WORLDIVES, el widget y la API.
Idiomas: la ventana «Contrata tu seguro» y los avisos, en los 9 idiomas.
Capturas:
«Mi seguro de buceo» en sus cuatro estados;
la ventana de contratar;
el paso de la reserva con el seguro;
el participante con seguro caducado en el panel del centro;
la administración de aseguradoras.
Para que el titular lo pruebe (zip de pruebas)
buzo.prueba, con un seguro caducado;
buzo2.prueba, con uno vigente;
dos aseguradoras inventadas («Aseguradora Demo A» y «Demo B») con enlaces a una página de prueba;
un servicio del centro marcado «obligatorio».
Añadir a README-PRUEBAS.md la sección «Probar los seguros» con estos pasos:
reservar con buzo.prueba;
contratar el seguro de prueba y subirlo;
verlo en verde en el panel del centro.
Entrega conjunta (Bloques 1 y 2)
Todo en la próxima versión, en los dos zips.
Documentación:
docs/reservas/multicanal-estado-actual.md y docs/seguros/estado-actual.md (las dos Partes A);
docs/api/ con la API y los webhooks;
la guía para centros «Cómo poner WORLDIVES en tu web».
Notas de versión con dos apartados: «Motor de reservas multicanal» y «Seguros de buceo», cada uno con:
la tabla de estado de cada punto;
los resultados de las pruebas y las capturas.
Lista de pendientes de decisión del titular (acuerdos con aseguradoras, conexión con otras plataformas) y del abogado:
encargo de tratamiento de las reservas del widget;
papel de WORLDIVES en la distribución de seguros y su posible inscripción;
textos legales.