# Preguntas para la gestoría

Versión v50.38 · 11/10/2026
Estado: borrador para revisión

Dudas fiscales y contables de WORLDIVES DISCOVERY antes del lanzamiento. Cada pregunta explica primero qué hace hoy la web (con la parte del código en que se apoya) y luego qué hay que decidir. Reúne también los puntos «Para gestoría» de las notas de versión (`RELEASE_NOTES_v50_34.md` y `v50_37.md`) y los **[PENDIENTE GESTORÍA]** de `docs/legal/*.md`.

Datos del titular: `{{owner_name}}`, NIF `{{nif}}`, domicilio `{{address}}` ([pendiente de completar]).

## 0. Cómo gana dinero la web

| Concepto | Quién paga | Cómo se cobra | Dónde queda registrado |
|---|---|---|---|
| **Cuota anual de plan** («Motor de reservas» o «Pro», 12 meses por adelantado, sin renovación automática) | Centros de buceo y profesionales independientes («freelance»), de España, de la UE y de fuera | Tarjeta con Stripe Checkout **en la cuenta de WORLDIVES**, o transferencia que la administración anota a mano | `plan_payments` (`method='stripe'` o `'manual'`), email `plan_paid` |
| **Patrocinios** (ofertas destacadas y banda de patrocinadores en la portada) | Marcas, empresas o centros | Fuera de la web (se acuerda y cobra aparte) | `sponsorships` (anunciante, fechas, importe y moneda, solo como nota) |
| Reservas de los buceadores | Buceadores | Cargo directo de **Stripe Connect en la cuenta del centro o del freelance**. El dinero nunca pasa por WORLDIVES | `payment_orders` |
| Comisión por reserva | — | **No existe** | `comisiones = 0` en el informe DAC7 |

- La ficha gratuita no tiene coste. Al aprobar un centro se le da una **prueba de 60 días** del plan Pro (`plans_trial_days`).
- Los precios de los planes aún no están fijados (`PLAN_DEFAULTS`, `price_year = None`). La moneda por defecto es EUR, pero cada plan puede tener otra (`plans.currency`).
- Los **puntos** del programa de fidelización (1:1, antes «monedero») no son dinero ni se pueden cobrar; los canjes son ventajas que da cada centro.

## 1. Alta y forma jurídica

1. **¿Autónomo o sociedad limitada?** Con ingresos solo por cuotas anuales y patrocinios, ¿qué conviene al empezar? ¿Qué cambia en DAC7, Verifactu y en la responsabilidad?
2. **Epígrafe del IAE.** ¿Cuál corresponde a una plataforma web que cobra suscripciones a empresas por un software de reservas y publica anuncios patrocinados? (por ejemplo, servicios de informática o de publicidad). ¿Uno o dos epígrafes?
3. **Modelo 036/037.** Además del alta, ¿hay que darse de alta en el **ROI** (Registro de Operadores Intracomunitarios) desde el principio, dado que habrá clientes empresariales de la UE y proveedores extranjeros (Stripe en Irlanda, Esri y otros en EE. UU.)?
4. **Domicilio fiscal y web.** ¿Algún requisito para que el domicilio que figura en el aviso legal coincida con el fiscal?

## 2. IVA de la cuota anual

Hoy la sesión de pago de Stripe (`/api/provider/plan/checkout` en `app/server.py`, `stripe.checkout.Session.create`) cobra el importe del plan tal cual: **no calcula impuestos** (`automatic_tax` no se usa), **no pide el NIF-IVA** del cliente (`tax_id_collection` no se usa) ni su dirección de facturación. Las condiciones para centros (`app/legal/es/centros.md`, cláusula 3) remiten a la página de planes para el precio y no dicen si incluye IVA.

1. **Precio con o sin IVA.** Los clientes son empresas y profesionales. ¿Se publica el precio sin IVA («+ IVA») o con IVA incluido? ¿Cómo se muestra a clientes de otros países?
2. **Clientes en España:** ¿21 %? ¿Algún caso especial (Canarias, Ceuta, Melilla, con IGIC o IPSI)?
3. **Clientes de la UE con NIF-IVA válido (B2B):** ¿factura sin IVA con **inversión del sujeto pasivo** (art. 69 y 84 LIVA)? ¿Hay que comprobar el número en **VIES** en cada cobro y guardar la prueba? ¿Modelo **349**?
4. **Clientes de la UE sin NIF-IVA** (por ejemplo, un freelance que no esté registrado): ¿se tratan como consumidores? Si la cuota es un **servicio prestado por vía electrónica**, ¿tributa en el país del cliente y hay que usar la **ventanilla única (OSS)**? ¿Hay umbral de 10 000 €?
5. **Clientes de fuera de la UE** (Egipto, Indonesia, México…): ¿no sujeto en España? ¿Qué mención lleva la factura? ¿Riesgo de que el país del cliente exija IVA o retención por servicios digitales?
6. **¿Es la cuota un servicio electrónico** (software como servicio, en gran parte automatizado) o un servicio de publicidad/intermediación? ¿Cambia el lugar de realización?
7. **Prueba gratuita de 60 días y asignaciones manuales** sin cobro (`/api/admin/plans/assign` con importe 0, excepciones de funciones): ¿alguna consecuencia (autoconsumo, operaciones gratuitas)?
8. **Moneda distinta del euro:** si un plan se cobra en USD, ¿qué tipo de cambio se usa para declarar?
9. **Qué datos debe pedir la web** para resolver todo lo anterior: país, NIF-IVA, razón social, dirección fiscal. Hoy existen en la ficha del prestador (`FISCAL_FIELDS`: `legal_name`, `tax_id`, `tax_id_country`, `fiscal_address`, `entity_type`, `registration_number`, `birth_date`…) para DAC7, pero el pago de la cuota **no los usa**.

## 3. Facturas de la cuota y Verifactu

Hoy la web registra el pago (`plan_payments`: importe, moneda, método, estado, periodo, fecha de pago) y envía el correo `plan_paid`, pero **no emite facturas**. Stripe Checkout tampoco genera factura (no se usa `invoice_creation`). La administración ve los 100 últimos pagos y no hay exportación de `plan_payments`.

1. ¿Hay que emitir **factura completa** por cada cuota (sí parece, al ser empresas)? ¿Desde la web, desde Stripe (Stripe Invoicing) o desde un programa de facturación aparte?
2. **Verifactu** (Real Decreto 1007/2023): ¿desde qué fecha aplica a WORLDIVES según sea autónomo o sociedad? Si la factura se emite desde la web, el sistema de facturación debe cumplir el reglamento (registros encadenados, QR, envío a la AEAT o modo no verifactu). ¿Se recomienda usar un programa homologado externo en lugar de programarlo?
3. **Factura electrónica B2B** (Ley 18/2022 «Crea y Crece»): ¿cuándo será obligatoria y qué formato?
4. **Transferencias anotadas a mano** (`method='manual'`): ¿qué justificante hay que guardar?
5. **Numeración y series:** ¿una serie para cuotas y otra para patrocinios? ¿Rectificativas cuando se cancela un plan (la web no prevé devoluciones de cuota)?
6. **Patrocinios:** factura aparte; IVA según el país y tipo del anunciante (publicidad B2B).

## 4. DAC7

El código genera un informe anual (`dac7_report()`, *Administración → DAC7*, `/api/admin/dac7`, CSV `dac7-AAAA.csv`) con una fila por prestador y moneda: razón social, persona física o jurídica, NIF/TIN y país, registro mercantil, fecha de nacimiento, dirección, cuenta de cobro, **importes cobrados online por trimestre menos devoluciones**, número de actividades por trimestre, comisiones (siempre 0) e impuestos retenidos (0). Deja fuera a los prestadores sin cobros online y marca los datos incompletos. Las condiciones para centros (cláusula de DAC7) dicen «si la ley nos obliga, comunicaremos a la Agencia Tributaria…».

1. **¿Es WORLDIVES «operador de plataforma» obligado** (Directiva (UE) 2021/514, Ley 13/2023 y Real Decreto 117/2024)? La web permite a los vendedores ofrecer servicios y cobrar, pero los cobros son **cargos directos en la cuenta Stripe del centro** y WORLDIVES no cobra comisión. ¿Basta que la plataforma «permita» la venta, aunque no cobre ni conozca la contraprestación por sí misma? ¿Y los centros que cobran en el mostrador (sin pago online)?
2. **Modelo 040** (declaración censal de operadores de plataforma): ¿hay que presentarlo antes de empezar?
3. **Modelo 238**: formato del fichero, plazo (enero del año siguiente), si el CSV actual sirve de base y si hay que presentar declaración negativa en los años sin datos.
4. **Prestadores excluidos**: entidades cotizadas, entidades públicas, ¿menos de 30 operaciones y 2000 € (solo para venta de bienes)? ¿Aplica alguna exclusión a nuestros centros?
5. **Actividad prestada fuera de la UE** por centros de fuera de la UE con buceadores europeos: ¿se declara?
6. **Diligencia debida:** ¿qué hay que comprobar del NIF y la dirección del prestador? ¿Qué pasa si no da los datos (la web hoy solo los marca como incompletos)?
7. **Conservación:** ¿10 años para los datos DAC7 (según la Directiva)?
8. **Moneda:** ¿los importes en USD o en otras monedas se convierten a euros? ¿Con qué tipo?

## 5. Gastos y facturas de proveedores

1. **Stripe por la cuota.** Stripe Payments Europe (Irlanda) cobra a WORLDIVES sus comisiones por cada cuota pagada con tarjeta. ¿Están exentas de IVA (servicios financieros) o sujetas con inversión del sujeto pasivo? ¿Dónde se descargan y cómo se contabilizan (importe bruto cobrado, comisión descontada en la liquidación)?
2. **Stripe Connect.** Las cuentas conectadas pagan sus propias comisiones (`stripe_controller()`, `fees.payer = 'account'` por defecto). Si alguna vez se configurase `fees.payer = 'application'`, Stripe facturaría a WORLDIVES. Confirmar que hoy WORLDIVES no tiene ningún coste por las reservas de los centros.
3. **Proveedores extranjeros:** Esri (satélite, EE. UU.), alojamiento del servidor, correo (Brevo, Francia, recomendado), dominio. ¿Inversión del sujeto pasivo en el modelo 303 y declaración en el **349** (los de la UE)?
4. ¿Qué gastos de puesta en marcha son deducibles (desarrollo, diseño, licencias de imágenes)?

## 6. Justificantes de reserva

Los buceadores reciben un **justificante en PDF**, no una factura. Las condiciones para centros dicen: «si tu actividad lo exige, la factura la emites tú».

1. ¿Es suficiente un justificante para el buceador? ¿Qué datos fiscales mínimos debe llevar del prestador (razón social, NIF, dirección)? (Nota de v50.34.)
2. ¿Tiene WORLDIVES alguna obligación de facturar en nombre del centro (facturación por terceros) o de avisarle de que emita la factura?

## 7. Declaraciones y conservación

1. Calendario de declaraciones que tocarán: 303 (trimestral), 349, 390, 130 o 202 según forma jurídica, 111 si hay nóminas o profesionales, 347, 040 y 238 si aplica DAC7. Confirmar la lista.
2. **Conservación de documentos:** ¿6 años (Código de Comercio) para pagos y contabilidad; 4 años (prescripción tributaria); 10 años DAC7? Hoy la web **nunca borra** `plan_payments`, `payment_orders` ni `bookings` (`run_retention_jobs()` no los toca). ¿Correcto?
3. ¿Qué informes debe poder sacar la web para la contabilidad (exportación de `plan_payments` y `sponsorships`, por trimestre y por país del cliente)? Hoy no existe.

## 8. Otros

1. **Puntos de fidelización:** ¿alguna consecuencia fiscal para WORLDIVES? No tienen valor monetario ni los paga WORLDIVES; los canjes son ventajas de los centros.
2. **Conversión del antiguo monedero a puntos 1:1** (`RELEASE_NOTES_v50_35.md`): no había dinero real detrás en la base entregada; confirmar que no hay nada que regularizar.
3. **Patrocinios de centros** que a la vez pagan cuota: ¿una factura o dos?

## 9. Origen de cada punto

| Origen | Puntos |
|---|---|
| `RELEASE_NOTES_v50_34.md` («Para abogado / gestoría») | 6.1 |
| `RELEASE_NOTES_v50_37.md` («Para abogado / gestoría») | 2, 3, 4 |
| `docs/legal/condiciones-centros.md` (desajuste 6 y puntos pendientes) | 2, 3, 4 |
| `docs/legal/registro-actividades-tratamiento.md` | 4.7, 7.2 |
| Encargo, Fase 8 punto 15 | 1, 2, 4 |
