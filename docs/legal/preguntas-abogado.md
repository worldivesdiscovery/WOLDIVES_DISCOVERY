# Preguntas para el abogado

Versión v50.38 · 11/10/2026
Estado: borrador para revisión

Lista única de las dudas jurídicas de WORLDIVES DISCOVERY antes del lanzamiento. Cada pregunta explica primero qué hace hoy la web (con la parte del código en que se apoya) y luego qué hay que decidir. Reúne también todos los puntos «Para abogado» de las notas de versión (`docs/notas-de-version/v50.31.md` … `v50_37.md`), de `docs/*.md` y los **[PENDIENTE ABOGADO]** de `docs/legal/*.md`.

Los textos publicados están en `app/legal/es/*.md` (castellano, referencia) y `app/legal/en/*.md` (inglés, oficial). Cada uno tiene su ficha de revisión en `docs/legal/`.

## 0. Contexto en una página

- **Qué es:** directorio y motor de reservas de buceo. Catálogo de puntos de buceo, fichas de centros y profesionales independientes («freelance»), reservas de salidas y cursos, viajes y experiencias, reseñas y un programa de puntos.
- **Papel elegido por el titular:** intermediario tecnológico. El centro o el profesional presta la actividad y responde de ella.
- **Ingresos:** solo la **cuota anual** de los planes (`plans`, `plan_payments`) y patrocinios contratados aparte (`sponsorships`). **Ninguna comisión** por reserva.
- **Cobros:** cargos directos de **Stripe Connect** en la cuenta del centro o del profesional. Cada uno tiene su cuenta, paga sus comisiones de Stripe, y Stripe asume los saldos negativos (`losses.payments = 'stripe'`). WORLDIVES no toca el dinero de las reservas.
- **Documentos al buceador:** justificantes en PDF, no facturas.
- **Mensajes:** no es una red social. Solo avisos ligados a una reserva y reseñas con una respuesta pública del centro.
- **Salud:** no se suben certificados médicos (`MEDICAL_WORDS`, `test_g6_no_medical_certificates`).
- **Datos del centro:** son suyos y los exporta siempre (`/api/center/export`).
- **Idiomas:** 10; castellano e inglés son los oficiales.
- **Producción** empieza con la base limpia: los centros PADI/SSI importados son solo de demostración.

## 1. Papel de cada parte en protección de datos

Fichas relacionadas: `anexo-encargado-tratamiento.md`, `registro-actividades-tratamiento.md`, `condiciones-centros.md`.

1. **Centro y profesional como responsables independientes.** Cuando un buceador reserva, el centro recibe nombre, email, teléfono, titulación, participantes, notas, tallas de equipo, lastre habitual y contacto de emergencia (`bookings`, `user_profiles`). La ficha completa solo se ve si el buceador ha reservado él mismo o la ha compartido con el QR de check-in. ¿Es correcto calificar al centro como **responsable independiente** de esos datos y a WORLDIVES como responsable de la cuenta del buceador? ¿Hace falta un acuerdo de comunicación de datos entre ambos?
2. **WORLDIVES como encargado del centro.** Para las herramientas de gestión (clientes importados por CSV, reservas manuales, planning, iCal, notas, avisos y correos por cuenta del centro, cobros en mostrador, equipo) WORLDIVES trata datos que el centro decide. ¿Es encargado (art. 28 RGPD)? Si es así, el anexo de `anexo-encargado-tratamiento.md` no está publicado ni se acepta: ¿va como anexo de las condiciones para centros (`centros.md`, aceptación en `legal_acceptances`) o como documento aparte?
3. **Solicitudes de información** (`info_requests`, `POST /api/info-requests`). El formulario está en la web de WORLDIVES, pide aceptar su privacidad y una casilla para enviar los datos al centro, que los recibe por email (`info_request`). ¿WORLDIVES es responsable que comunica, o encargado del centro? ¿Basta el consentimiento de la casilla?
4. **Freelance.** El profesional independiente cobra con su propia cuenta Stripe y puede trabajar además para un centro como miembro de su equipo. ¿Mismo papel que un centro? ¿Cambia algo cuando actúa como empleado?
5. **Stripe en cargos directos.** Stripe Payments Europe recibe los datos del pago en la cuenta conectada del centro; WORLDIVES crea la sesión de pago con su clave de plataforma y ve el estado del pago, la marca y los últimos 4 dígitos (`payment_orders`). ¿Stripe es responsable independiente, encargado del centro o subencargado de WORLDIVES? ¿Cómo se califica el acceso de WORLDIVES a los datos de la cuenta conectada? Hoy Stripe **no figura como subencargado** en el anexo.
6. **Ficha compartida por QR** (`data_shares`): el buceador comparte su ficha con un centro haciendo check-in. ¿Comunicación entre responsables o encargo?
7. **Personal de WORLDIVES** (administradores): informar aparte de su tratamiento.
8. **Personal del centro.** Las cuentas del equipo (`center_members`, roles propietario, recepción e instructor) son cuentas personales de los empleados. ¿Qué papel tiene WORLDIVES con sus datos y con el registro de actividad que ve el propietario?
9. **Transferencias a centros fuera del EEE** (Egipto, Indonesia, México…). ¿Sirve el art. 49.1.b RGPD (necesario para el contrato pedido por el interesado)? ¿Cómo se informa?
10. **Delegado de protección de datos.** ¿Confirmar que no es obligatorio (art. 37 RGPD, art. 34 LOPDGDD)?
11. **Conservación.** Plazos configurables (`RETENTION_DEFAULTS`): cuentas inactivas 36 meses con aviso 30 días antes, documentos caducados 12 meses, avisos 24 meses, auditoría 12 meses. Reservas y pagos **no se borran nunca**. Denuncias (`content_reports`) y pruebas de consentimiento (`consent_log`) tampoco; la privacidad dice «hasta 5 años». ¿Plazos correctos? ¿Quién conserva reservas y pagos tras la baja de un centro, él o WORLDIVES, y cuánto tiempo?
12. **Documento de identidad.** Se puede subir como documento del buceador. ¿Es proporcional (minimización) o se debe quitar?
13. **Responsabilidad entre las partes, costes de auditoría y ley aplicable del anexo** (las condiciones para centros remiten a la ley española). ¿Prevalencia del anexo sobre las condiciones?
14. **Brechas.** En `procedimiento-brechas.md`: criterios de riesgo, cuándo no hace falta avisar a los afectados, autoridad principal con afectados de otros países (AEPD si el establecimiento está en España), plazo para avisar a los centros como responsables, y si aplica NIS2 (en principio no, por tamaño).
15. **GEBCO y Nominatim.** No se envían datos personales; ¿hace falta mencionarlos como destinatarios?

## 2. Datos de salud

1. **Sin certificados médicos.** El servidor rechaza documentos médicos (`DOCUMENT_TYPES` sin certificado, palabras de `MEDICAL_WORDS`); la web dice «entrégalos directamente al centro». Al actualizar se borró cualquiera que existiera. ¿Suficiente para afirmar que WORLDIVES no trata datos de salud?
2. **Campos dudosos del perfil** (`user_profiles`): fecha de nacimiento, **lastre habitual en kg** (`usual_weight_kg`, no es el peso corporal), contacto de emergencia (nombre y teléfono) y notas libres. ¿Alguno puede considerarse dato de salud o revelarla indirectamente?
3. **Contacto de emergencia.** Son datos de un tercero que el buceador introduce. ¿Cómo se cumple el art. 14 RGPD? ¿Basta con avisar al buceador de que informe a esa persona?
4. **Notas libres** (perfil, reserva, fichas de cliente importadas) no se filtran. El anexo obliga al centro a no introducir datos de salud. ¿Basta esta obligación contractual?
5. **Declaración médica del centro.** El centro puede pedir su propio cuestionario médico en persona. ¿Debe la web decir algo más sobre ello en las condiciones de reserva (cláusula 7)?

## 3. Viajes combinados y servicios de viaje vinculados

1. **Un proveedor por experiencia.** Cada viaje o experiencia (`travel_experiences`) tiene un único prestador (`provider_user_id` o `center_id`). WORLDIVES no combina servicios de varios proveedores ni vende alojamiento o transporte propio. El bloque legal de cada experiencia dice «Prestado por … WORLDIVES DISCOVERY es la plataforma de reservas: no organiza ni presta la actividad». ¿Basta para quedar fuera de la Directiva (UE) 2015/2302 y del libro IV del TRLGDCU como organizador o minorista?
2. **El centro que vende un paquete.** Si un centro publica un viaje que incluye alojamiento y buceo, ese centro es el organizador. ¿Debe la web exigirle que declare que tiene licencia de agencia y la garantía obligatoria? ¿Qué responsabilidad tiene WORLDIVES si no la tiene?
3. **Servicios de viaje vinculados.** Un buceador puede reservar un viaje de un centro y luego otra actividad de otro centro en la misma sesión. No hay carrito común ni pago conjunto. ¿Descarta esto el «servicio de viaje vinculado»?
4. **Lenguaje.** Los correos de experiencias llaman «organizador» al centro (`experience_request`). ¿Conviene cambiar la palabra?

## 4. Ley aplicable y consumidores extranjeros

1. **Roma I, art. 6.** Las condiciones remiten a la ley española. Los buceadores son de muchos países y la web está en 10 idiomas. ¿Qué cláusula de ley aplicable y jurisdicción es válida frente a un consumidor de otro Estado de la UE que «dirige» la web a su país?
2. **Actividades prestadas fuera de España** por centros extranjeros: ¿qué ley rige el contrato buceador–centro? ¿Debe la web informar de ella antes de reservar?
3. **Idioma de prevalencia.** Castellano e inglés son oficiales; los otros 8 idiomas son traducciones y la web muestra encima «en caso de discrepancia prevalece el castellano». Pero 4 textos en inglés (`centros`, `denuncias`, `aviso-legal`, `seguridad`) también llevan dentro la frase «the Spanish version prevails», lo que contradice que el inglés sea oficial. ¿Se quita esa frase del inglés, o el inglés pasa a ser también traducción? ¿Es válida la nota de prevalencia frente a consumidores (art. 5 Directiva 93/13: interpretación más favorable)?
4. **Reclamaciones.** Las condiciones de reserva remiten a email con la referencia `WOD-…`, mediación con el centro y hojas oficiales. ¿Qué debe ofrecer WORLDIVES (ODR/plataforma de resolución de litigios, entidades de resolución alternativa)?

## 5. Responsabilidad como intermediario

1. **Exención de alojamiento** (art. 6 DSA). ¿Se mantiene con la verificación de centros, la banda «Centros asociados», el orden «Recomendados» y la etiqueta «Verificado»? ¿La verificación hace pensar a un consumidor medio que WORLDIVES responde del centro (art. 6.3 DSA)?
2. **Información de los puntos de buceo** (profundidad, nivel, corrientes, descripciones reescritas). Es orientativa. ¿Qué cláusula de limitación es válida?
3. **Stripe con `losses.payments = 'stripe'`.** ¿Qué responsabilidad le queda a WORLDIVES frente a Stripe y frente al centro por saldos negativos, disputas o fraude?
4. **Devolución no hecha.** Si el buceador cancela dentro de plazo, la web **propone** la devolución al centro (`propose_refund()`), le recuerda a las 72 h (`run_refund_reminders()`) y la administración marca incidencias (`/api/admin/payments/incident`) sin mover dinero. ¿Qué responsabilidad tiene WORLDIVES si el centro no devuelve? ¿Debe poder suspender sus cobros online? **[PENDIENTE TITULAR]** decide la medida.
5. **Cancelación por el centro.** El texto dice que devuelve el 100 %; el código propone el 100 % pero deja al centro poner menos (`refund_amount`). ¿Se limita en el servidor o se explica en el texto?
6. **Suspensión de cuentas.** Las condiciones dicen que se pueden suspender o cerrar cuentas con motivos (y para centros, 30 días, art. 4 P2B). No hay herramienta en el código. ¿Riesgo de publicarlo así hasta que exista?

## 6. Señal, cancelaciones y desistimiento

1. **Art. 103.l) TRLGDCU.** Las condiciones de reserva excluyen el desistimiento de 14 días por ser servicios de ocio con fecha. ¿Cubre cursos de varios días y viajes? ¿Cómo debe informarse antes de pagar (hoy se muestra la política en la reserva, `booking_policy()`, `booking_cancel_terms()`)?
2. **Política de cada centro.** El centro fija horas de cancelación gratuita y porcentaje de devolución fuera de plazo (`cancel_free_hours`, `cancel_refund_pct`); la reserva guarda una copia. ¿Es válido un 0 % fuera de plazo? ¿Límites de la cláusula penal en consumo (art. 85.6 y 87 TRLGDCU)?
3. **Señal.** Fija **por persona** o porcentaje (`deposit_type`, `deposit_value`); el resto se paga en el centro («Cobrar el resto», estado `deposit_paid`). ¿Cómo se califica la señal (arras penitenciales, confirmatorias o pago a cuenta)? ¿Debe decirse expresamente si se pierde al cancelar?
4. **Modo «Bajo petición».** El centro acepta o rechaza con plazos (`response_hours`, `payment_hours`); si rechaza, se devuelve lo cobrado (`reject_booking()`). ¿Cuándo se perfecciona el contrato?
5. **Justificante, no factura.** ¿Es suficiente para el buceador? ¿Qué datos fiscales mínimos debe mostrar el prestador en el justificante?

## 7. Reglamento de servicios digitales (DSA)

Ver `procedimiento-denuncias.md`.

1. ¿WORLDIVES es **plataforma en línea** y **mercado en línea**?
2. ¿Puede acogerse a la **exención de micro y pequeñas empresas** (art. 19 y 29) y desde cuándo? ¿Qué sigue aplicando (arts. 11–18 y 24.3)? ¿Aplica el art. 24.2 (cifra de destinatarios activos cada seis meses)?
3. **Informe de transparencia** (art. 15): ¿exento? Si no, se puede sacar de `content_reports` y `audit_log`.
4. **Declaración de motivos** (art. 17): los correos `report_resolved` y `report_decision_affected` dan la decisión, los motivos (obligatorios desde v50.38, mínimo 10 caracteres), la opción de responder al correo y, desde v50.38, la mención a los órganos de resolución extrajudicial certificados y a los tribunales (arts. 20 y 21). El correo al denunciante va en su idioma. ¿Falta algo (tipo de restricción, si la decisión fue automatizada)?
5. **Recurso por respuesta al correo** en lugar de un sistema interno de reclamaciones (art. 20): ¿suficiente si se está exento? ¿Plazo?
6. **Denuncias anónimas.** Desde v50.38 el nombre y el email son obligatorios (art. 16.2.c), como dice el texto. Excepción del art. 16.2.c para contenidos de abuso sexual de menores: hoy también exige nombre y email. ¿Se permite el anonimato solo para ese motivo?
7. Coordinador de servicios digitales en España, alertadores fiables y órdenes de autoridades: confirmar el procedimiento.

## 8. Reglamento P2B (UE) 2019/1150

Ver `condiciones-centros.md`.

1. **Clasificación** (art. 5). `#/legal/clasificacion` explica el orden «Recomendados»; el código (`DIRECTORY_SORT_KEYS['recommended']`) usa, por este orden: tiene servicios publicados, tiene salidas programadas próximas (`next_slot`), número de reseñas, foto de portada y nombre. Los planes **no** cambian el orden. ¿Es suficiente la descripción? (Hay que corregir una frase: el texto dice «aceptan reservas online».)
2. **Contenido patrocinado.** Ofertas destacadas y banda de patrocinadores con etiqueta «Patrocinado» que no se puede quitar y no cambia el orden. ¿Correcto según P2B y Ómnibus? (El titular debe elegir «Patrocinado» o «Destacado».)
3. **Aviso de 15 días** para cambiar las condiciones (`LEGAL_NOTICE_DAYS = {'centros': 15}`, `notify_legal_change()`, barra del panel y nueva aceptación). ¿Cumple el art. 3? ¿Qué pasa si el centro no acepta?
4. **Restricción, suspensión y cierre** (art. 4): motivos y 30 días. Sin herramienta en el código.
5. **Trato diferenciado** (art. 7) entre planes y frente a contenidos de WORLDIVES.
6. **Acceso a datos** (art. 9): el centro exporta siempre sus datos (CSV y ZIP).
7. **Reclamaciones internas** (art. 11): solo email. ¿Hace falta un sistema? ¿Exento por pequeña empresa (art. 11.5)?
8. **Mediadores** (art. 12): hay que **nombrar al menos dos**; el texto solo dice «podrán acudir a mediación». ¿Cuáles? ¿Exención por tamaño?

## 9. Planes, degradación y cuotas

1. **Planes** (`PLAN_DEFAULTS`): ficha gratuita, «Motor de reservas» y «Pro», con límites de servicios y equipo. Prueba de 60 días de Pro al aprobar el centro. Precios aún sin fijar (`price_year = None`). ¿Qué debe decir el contrato sobre renovación, cambios de precio y prueba gratuita?
2. **Degradación** al terminar el plan: la ficha queda gratuita con «Solicitar información», las reservas existentes se atienden, se bloquean iCal y cobros online nuevos, la exportación sigue. ¿Es una práctica engañosa para el buceador ver un centro sin reserva online? ¿Está bien explicada la retirada de funciones al centro?
3. **Excepciones y asignación manual** por la administración, con motivo. ¿Riesgo de trato desigual (P2B art. 7)?
4. **Sin comisión.** ¿Algún riesgo en afirmarlo si los patrocinios son de pago?

## 10. Cuentas del equipo e importación de clientes

1. **Equipo** (`center_members`, `TEAM_ROLES`: propietario, recepción, instructor; `team_gate()` limita permisos). ¿Responde el centro de todo lo que hacen sus empleados (cláusula 9)? ¿Cuentas personales de empleados para uso profesional: algo que añadir?
2. **Importación de clientes** (`import_clients()`, CSV con nombre, email, teléfono, titulación y notas). No se convierten en cuentas ni reciben comunicaciones comerciales. La web **no pide** al centro que declare su base legal. ¿Qué base legal tiene el centro y debe declararla al importar?
3. **Feed iCal** privado con las reservas en curso (nombres de clientes en el calendario externo del centro). ¿Algún aviso necesario?

## 11. Reseñas verificadas (Directiva Ómnibus)

1. Solo puede reseñar quien tenga una reserva **pagada o confirmada** con el centro (no hace falta que esté completada). Las cuentas de centro, profesional (freelance, desde v50.38) y administración no pueden reseñar. Una reseña ocultada por moderación sigue oculta aunque su autor la edite (corregido en v50.38). Una reseña por buceador y centro; se puede editar. La etiqueta de cada reseña dice «✓ Inmersión verificada», pero se puede reseñar **antes** de la actividad (`normas-resenas.md`, desajuste 3). ¿Basta para llamarlas «verificadas» (art. 20.7 TRLGDCU tras la Ley 4/2022 y el RDL 24/2021)? ¿Debería exigirse la reserva **completada** o cambiar la etiqueta a «reserva verificada»?
2. **Normas de reseñas** (`resenas.md`): ¿informa suficientemente de cómo se comprueban (art. 5.6 Directiva 2005/29 tras Ómnibus)?
3. **Invitación a reseñar** por email tras la reserva (plantilla `review_request`): ¿interés legítimo o consentimiento? No hay casilla de oposición en la web: ¿debe el email llevar un enlace para no recibir más?
4. **Respuesta del centro**: una por reseña, pública, avisa al autor (`review_replied`). Freelance sin centro no recibe reseñas, pero `resenas.md` habla de «centro o profesional». ¿Se corrige el texto?
5. **Moderación**: ocultar con motivo enviado al autor (`/api/admin/reviews/<id>/moderate`). ¿Algo más?
6. **Responsabilidad** de WORLDIVES por el contenido de reseñas y respuestas (art. 6 DSA) y plazo de conservación de las reseñas ocultas.

## 12. Comunicaciones comerciales y consentimiento

1. Consentimiento separado y registrado (`consent_log`, `kind='marketing'`); baja en un clic sin sesión; pie del correo «Recibes este correo porque aceptaste…». ¿Cumple LSSI art. 21 y RGPD? ¿Texto de la casilla correcto?
2. Los correos de los centros a sus clientes importados no existen como campañas. ¿Se puede ofrecer en el futuro y con qué base?
3. Plazo de conservación de `consent_log` (hoy sin borrado).

## 12 bis. Cookies y terceros

Ficha: `cookies-terceros.md`.

1. ¿Todo el almacenamiento listado es técnico y exento (art. 22.2 LSSI-CE, Guía de cookies de la AEPD de 2023), incluidos `wd_top10` (preferencia del usuario) y la caché del service worker?
2. Si no hay cookies que requieran consentimiento, ¿basta un aviso informativo con un solo botón («Entendido»)?
3. **GEBCO** (servidores del British Oceanographic Data Centre, Reino Unido): la IP sale al cargar la capa que el visitante elige. ¿Basta con informar (decisión de adecuación para el Reino Unido)?
4. **Vídeos tras clic**: ¿vale el botón «Cargar vídeo» con el aviso actual como consentimiento para las cookies de Vimeo o Google Maps? (YouTube se usa en modo sin cookies.)
5. **Cookies de Stripe** en su página de pago: ¿basta con mencionarlas como responsabilidad de Stripe?

## 13. Menores

1. Las condiciones exigen 18 años; el registro tiene una casilla y no pide fecha de nacimiento. ¿Suficiente? (El art. 7 LOPDGDD fija 14 años para el consentimiento.)
2. Un adulto reserva para varias personas (`participants`) sin nombres; pueden ser menores. ¿Cómo acepta el adulto las condiciones del centro en nombre del menor? ¿Debe la web pedir algo (edad mínima de la actividad, autorización)?

## 14. Catálogo, imágenes y mapas

1. **Lista de 215 puntos de buceo** (nombres y coordenadas). ¿Viene de un listado de PADI u otra base con derechos *sui generis* (Directiva 96/9/CE)? Si es así, ¿basta con verificar los puntos con fuentes abiertas (OpenStreetMap, cartografía oficial)? Ver `catalogo-origen.md`.
2. **Descripciones reescritas** con texto propio (283; ver `puntos-reescritos.md`). ¿Suficiente para evitar infracción?
3. **Centros PADI/SSI importados**: solo en demostración. Confirmar que no hay riesgo si nunca pasan a producción.
4. **Licencias de las 23 imágenes** (`imagenes-origen.md`): cada una necesita origen comprobado (propia, banco con licencia o cesión por escrito).
5. **Contenido de centros y usuarios**: licencia que conceden (aviso legal, cláusula 3), alcance «mientras sigan publicados», traducciones automáticas y banda «Centros asociados».
6. **Logo del centro** fuera de su ficha: consentimiento por casilla (`logo_consent`, `logo_consent_at`, `audit_log`). ¿Suficiente y revocable?
7. **Esri (ArcGIS Location Platform).** La vista satélite se sirve por un proxy propio con la clave oculta, contador y límite mensual, y caché de 24 h en el navegador (`docs/mapas.md`). ¿Lo permiten los términos de Esri? ¿Atribución correcta? Alternativa: clave restringida al dominio cargada en el navegador.
8. **Protomaps y GEBCO**: confirmar atribuciones en `#/legal/creditos`.
9. **Marca «WORLDIVES DISCOVERY»**: comprobar registro en OEPM/EUIPO antes de afirmar que es del titular.

## 15. Programa de puntos

1. El antiguo monedero pasó a **puntos 1:1** sin valor monetario, canjeables solo por ventajas de centros, con caducidad (`puntos.md`). ¿Encaje como programa de fidelización? ¿Queda fuera de dinero electrónico y de servicios de pago (incluida la conversión del saldo antiguo)?
2. ¿Información obligatoria sobre caducidad y anulación?

## 16. DAC7

El código genera un informe anual por prestador y trimestre (`dac7_report()`, `/api/admin/dac7`) con los importes cobrados online menos devoluciones, número de actividades y comisiones (0). Recoge los datos fiscales del prestador (`FISCAL_FIELDS`).

1. ¿WORLDIVES es «operador de plataforma» obligado (Directiva (UE) 2021/514, Ley 13/2023) si no cobra a través de la plataforma, sino que son cargos directos en la cuenta del centro? Ver también `preguntas-gestoria.md`.
2. Si lo es: ¿base legal para pedir y conservar 10 años los datos fiscales y la fecha de nacimiento del prestador? ¿Qué pasa si el prestador no los da?

## 17. Otros textos y obligaciones

1. **Aviso legal** (art. 10 LSSI): ¿hace falta autorización o colegiación (no parece)? ¿Número de IVA intracomunitario? ¿Basta con titular, NIF, domicilio y email en el pie, sin teléfono ni registro?
2. **Accesibilidad**: la web no es de una administración. ¿Obligaciones de la Ley 11/2023 (Acta Europea de Accesibilidad) para comercio electrónico? ¿Exención de microempresa?
3. **Revisión general** de todos los textos publicados (privacidad, cookies y terceros, condiciones de uso, de reserva y para centros, reseñas, puntos, accesibilidad, contacto, créditos), en particular plazos de conservación, base legal de la invitación a reseñar, datos que recibe el centro y transferencias internacionales (nota de v50.36).
4. Al cambiar las condiciones para centros, los centros deben **volver a aceptarlas** con 15 días de aviso (nota de v50.34): confirmar el procedimiento ya montado.

## 18. Origen de cada punto

| Origen | Puntos de esta lista |
|---|---|
| `docs/notas-de-version/v50.34.md` | 5.3, 5.4, 6.5, 17.4, cláusulas de cuota, cobros, devoluciones y disputas (6, 9) |
| `docs/notas-de-version/v50.35.md` | 15, 12.1 |
| `docs/notas-de-version/v50.36.md` | 1.11, 7, 11.3, 14.1, 14.4, 14.7, 17.2, 17.3 |
| `docs/notas-de-version/v50.37.md` | 1.3, 9, 10, 16 |
| `docs/mapas.md` | 14.7 |
| `docs/legal/anexo-encargado-tratamiento.md` | 1.2–1.5, 1.8, 1.11, 1.13, 2.4, 10.2 |
| `docs/legal/registro-actividades-tratamiento.md` | 1.9, 1.10, 1.12, 1.15, 2.3, 11.3, 12.3, 16.2 |
| `docs/legal/procedimiento-brechas.md` | 1.14 |
| `docs/legal/aviso-legal.md` | 14.5, 14.9, 17.1 |
| `docs/legal/condiciones-buceadores.md` | 3.1, 4.1, 5.2, 5.5, 6.1–6.2, 13 |
| `docs/legal/condiciones-centros.md` | 1.1–1.2, 5.3, 8, 9.2, 10.1, 14.6 |
| `docs/legal/catalogo-origen.md`, `imagenes-origen.md` | 14.1–14.4 |
| `docs/legal/procedimiento-denuncias.md` | 7 |
| `docs/legal/cookies-terceros.md` | 12 bis |
| `docs/legal/normas-resenas.md` | 11.1, 11.3, 11.6, 7 |
| `docs/legal/politica-privacidad.md` | 1.1–1.7, 1.9–1.12, 2.2–2.3, 11.3, 13.1 |

## 19. Encargo 2 (v50.39–v50.42): descargos, manifiesto, cambios y cancelaciones de salidas

Ver `docs/notas-de-version/v50.40.md` y siguientes.

1. **Descargo firmado con firma dibujada** (`waiver_signatures`). Se guardan:
   - versión, título y texto exacto;
   - nombre completo y trazos de la firma;
   - fecha y hora UTC;
   - reserva y plaza;
   - método («Mi reserva» o check-in);
   - quién lo registró, la IP en hash y el navegador.

   Se descarga en PDF. ¿Es suficiente como firma electrónica simple (Reglamento eIDAS, art. 25) para el fin que buscan los centros? ¿Hace falta enviar copia por email o un sellado de tiempo?
2. **Validez de un descargo de responsabilidad frente a consumidores** (art. 86 TRLGDCU: cláusulas abusivas que excluyen la responsabilidad). ¿Qué puede y qué no puede decir el texto? ¿Conviene ofrecer a los centros un texto base revisado?
3. **Cuestionario médico o preguntas de salud:** no hay ninguno. Está preparado y desactivado (`WAIVER_HEALTH_QUESTIONS = False`). ¿Se puede activar y con qué base jurídica (art. 9 RGPD), qué información previa y qué plazo de conservación?
4. **Responsable de los descargos, las firmas y el manifiesto:** el centro, con WORLDIVES como encargado. ¿Hay que añadirlo al anexo de encargado y al registro de actividades? ¿Cuál es el plazo de conservación de las firmas? Hoy se conservan mientras exista la reserva.
5. **Acompañantes menores de edad** en una reserva: ¿debe firmar el tutor?
6. **Contacto de emergencia en el manifiesto:** solo se muestra si el buceador ha compartido su ficha con el centro (mismas reglas que la ficha del buceador). ¿Basta con lo que dice la política de privacidad?
7. **Cancelación de una salida por el centro** (mal tiempo, mar): el consumidor elige entre otra fecha del mismo servicio y la devolución íntegra. Si no elige en 48 h (plazo configurable), se le devuelve automáticamente. ¿Cumple el TRLGDCU y la normativa de servicios de ocio? ¿Es razonable el plazo?
8. **Cambio de fecha con precio distinto:** hoy la reserva mantiene su precio y solo se informa de la diferencia. Si se decide cobrar o devolver la diferencia, ¿qué información previa hace falta?
9. **Lista de espera:** se guarda la cuenta, la salida, el número de personas y las fechas del aviso. Las plazas se guardan 2 h a la persona avisada. ¿Hay que mencionarlo en la política de privacidad y en las condiciones de reserva?
