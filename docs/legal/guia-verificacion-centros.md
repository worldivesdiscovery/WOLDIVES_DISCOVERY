# Guía de verificación de centros y profesionales

Versión v50.38 · 11/10/2026
Estado: borrador para revisión

Esta guía explica cómo la administración comprueba un centro de buceo o un profesional freelance antes de aprobar su cuenta. Se basa en el flujo real del código (`app/server.py`). Aprobar una cuenta le da acceso a reservas, clientes y cobros: es la decisión de seguridad más importante del día a día (fallo G2 del diagnóstico).

---

## 1. Cómo funciona en la web

### 1.1 Alta

1. La persona se registra en `#/registro` y elige «Centro de buceo» o «Profesional freelance». Llamada: POST `/api/auth/register`.
2. Para pedir una cuenta profesional, la web exige:
   - nombre del centro (solo para centros) y **teléfono de contacto**;
   - aceptar las condiciones para centros (`accept_pro_terms`, guardado en `legal_acceptances` como `centros`);
   - en **modo piloto** (*Administración → Funciones*), un **código de invitación** válido de la tabla `pro_invites` (`pro_signup_check()`). El código se gasta al usarlo.
3. Lo que crea el servidor:
   - la cuenta como **buceador** (`users.role='recreational'`), con `requested_role='center'` o `'freelance'`;
   - si es un centro, una **ficha nueva oculta** (`centers.active=0`, `verification_status='pending_provider'`). Nunca se enlaza con una ficha existente, ni siquiera si el teléfono coincide;
   - una solicitud en la tabla `center_claims` (`status='pending'`), con teléfono, ciudad, web, email y nota del solicitante.
4. Correos:
   - al solicitante, la bienvenida `welcome_pro` y la verificación de email;
   - a los administradores, `admin_new_pro` («Nueva cuenta profesional pendiente»).

Mientras está pendiente, la persona solo puede usar la web como buceador. No ve el panel del centro, no puede activar Stripe ni rellenar los datos fiscales: esas rutas exigen el rol `center` o `freelance`.

### 1.2 Revisión

- Pantalla: *Administración → Verificaciones* (`adminCenterClaims()` en `public/assets/js/world-dives-v8.js`).
- Datos: GET `/api/admin/center-claims` lista las solicitudes pendientes con:
  - nombre de la cuenta, email y teléfono indicado;
  - ciudad, web y nota;
  - fecha de la solicitud;
  - una marca **«email del dominio de la web»** (`email_matches_domain`) cuando el dominio del email coincide con el de la web indicada.
- Decisión: POST `/api/admin/center-claims/review` con:
  - `decision`: `approve` o `reject`;
  - `verification_method`: obligatorio para aprobar. Uno de los tres de `VERIFICATION_METHODS`:
    - `email_domain`: «Email del dominio del centro»;
    - `phone_call`: «Llamada al teléfono público del centro»;
    - `document`: «Documento (licencia, alta fiscal o registro)»;
  - `verification_note`: obligatoria para aprobar, mínimo 5 caracteres.
- Todo queda en `center_claims` (`verification_method`, `verification_note`, `reviewed_by_user_id`, `reviewed_at`) y en `audit_log` (`center_claim_reviewed`).

> Desde la v50.36 ya no hay «coincidencia sugerida» por teléfono (`suggested_center_id` se guarda vacío). El texto de ayuda de la pantalla todavía la menciona: ignóralo.

---

## 2. Lista de comprobación antes de aprobar

Haz las comprobaciones por este orden. Para aprobar basta **un** método del servidor, pero la práctica recomendada es combinar al menos dos: el que se anota y otro de apoyo.

### 2.1 Identidad y existencia

- [ ] El centro existe: web propia, ficha en Google Maps u otro directorio, fotos y dirección física coherente con la ciudad indicada.
- [ ] El nombre de la cuenta (persona) aparece vinculado al centro: web, redes o registro mercantil.
- [ ] El email del solicitante está verificado (`users.email_verified_at`). Si no, pídele que lo verifique antes de seguir.
- [ ] El centro no está ya dado de alta con otra cuenta: busca el nombre y la ciudad en *Administración → Centros*.

### 2.2 Email del dominio (`email_domain`)

- [ ] El email es del dominio de la web del centro (la marca «email del dominio de la web» lo indica, pero compruébalo tú).
- [ ] El dominio es del centro y no un servicio genérico (gmail, hotmail…). Puedes mirar el WHOIS o el pie de su web.
- [ ] Envía un correo a esa dirección pidiendo una respuesta concreta (por ejemplo, el código de la solicitud) y espera la respuesta.

### 2.3 Llamada al teléfono público (`phone_call`)

- [ ] Llama al teléfono que aparece **en la web oficial o en Google Maps del centro**, nunca al que la persona escribió en el registro. Pueden ser distintos a propósito.
- [ ] Pregunta por la persona solicitante y confirma que ha pedido el alta en WORLDIVES.
- [ ] Anota número, fecha, hora y quién atendió.

### 2.4 Documentos (`document`)

Pide los documentos por email a la dirección de la cuenta. **No hay un sitio en la web para subirlos antes de aprobar.** Guárdalos fuera de la web, en una carpeta con acceso limitado, el tiempo que fije el registro de actividades de tratamiento **[PENDIENTE ABOGADO]**.

- [ ] Alta fiscal (036/037, o el equivalente del país) o escritura o registro mercantil, con razón social y NIF que cuadren con el centro.
- [ ] Licencias de actividad o autorizaciones que exija la comunidad autónoma o el país (actividades subacuáticas, embarcación, compresor…) **[PENDIENTE ABOGADO]**: lista de licencias mínimas por país.
- [ ] Para freelance: titulación de instructor en vigor (PADI, SSI, CMAS, FEDAS…) y alta como autónomo o equivalente.
- [ ] **Certificado de seguro de responsabilidad civil** en vigor: aseguradora, número de póliza y fecha de caducidad.
  - Tras aprobar, el centro debe subirlo él mismo en *Panel → Datos fiscales y seguro* (`/api/provider/insurance-doc`) y poner la caducidad. La web avisa 30 y 7 días antes y al caducar (`run_insurance_alerts()`).

### 2.5 Stripe

- [ ] Antes de aprobar, no hay nada que comprobar: la cuenta conectada se crea después, desde el panel (`/api/payments/connect/onboard`).
- [ ] Después de aprobar, revisa en el panel de Stripe de la plataforma (*Connect → Cuentas*) que la cuenta del centro está verificada por Stripe (cobros y pagos activados). La web guarda el mismo estado en `centers.stripe_charges_enabled` y `stripe_payouts_enabled` (o en `users`, si es freelance).
- [ ] Si Stripe rechaza o restringe la cuenta, trátalo como una señal de alarma (sección 4).

### 2.6 Datos fiscales y declaraciones (Fase 6, después de aprobar)

Los datos fiscales se rellenan **después** de aprobar, en *Panel → Datos fiscales y seguro* (`/api/provider/fiscal`, `save_provider_fiscal()`):

- tipo de prestador (empresa o persona física);
- razón social;
- NIF/TIN y país emisor;
- registro mercantil (empresa) o fecha de nacimiento (persona física);
- dirección fiscal;
- declaraciones de licencias y de personal titulado (`declares_licences`, `declares_qualified_staff`, `licences_note`);
- seguro.

- [ ] En los 15 días siguientes a la aprobación, mira en *Administración → Planes* la lista de prestadores. Cada uno muestra los **datos fiscales que faltan** (`fiscal_missing`). Escribe a quien los tenga incompletos.
- [ ] Comprueba que la razón social y el NIF que declara coinciden con los documentos de la sección 2.4.
- [ ] Los datos fiscales son necesarios para el informe DAC7 de enero (*Administración → Planes → Informe DAC7*, columna `datos_incompletos`).

> No hay pantalla de administración con los datos fiscales de un centro concreto ni con su certificado de seguro. El certificado se descarga en `/api/admin/insurance-doc?type=center&id=<id>` (o `type=freelance&id=<id de usuario>`) con la sesión de admin. Los datos fiscales completos solo salen en el CSV de DAC7, y solo para prestadores con cobros online en ese año.

### 2.7 Logo y «Centros asociados»

- [ ] No hace falta pedir permiso para el logo al aprobar. El centro lo concede él mismo en su panel (casilla «Autorizo a WORLDIVES…», columnas `logo_consent` y `logo_consent_at`).
- [ ] Sin ese permiso, el logo **no** aparece en la banda «Centros asociados» de la portada (`_build_promos()` exige `logo_consent=1`). No uses logos de centros en publicidad ni redes sin ese permiso por escrito.

---

## 3. Qué escribir en la nota de verificación

La nota es la prueba de la diligencia de WORLDIVES. Escríbela para que otra persona pueda repetir la comprobación. Mínimo:

- **qué** se comprobó, **cuándo** y **cómo**;
- el dato concreto (número llamado, dominio, documento y su número);
- quién atendió o firmó;
- el segundo método, si lo hubo.

Ejemplos:

- `phone_call`: «Llamada al 965 000 000 (teléfono de su web y de Google Maps) el 12/10/2026 a las 11:20. Atendió Ana P., gerente; confirma que Juan G. es socio y ha pedido el alta. Apoyo: email del dominio @centro-ejemplo.es».
- `email_domain`: «Email juan@centro-ejemplo.es; dominio de la web centro-ejemplo.es (WHOIS a nombre de Centro Ejemplo SL). Respondió el 12/10 con el código de solicitud. Apoyo: CIF B00000000 en el registro mercantil».
- `document`: «Alta 036 de Juan G. (NIF 00000000X) y titulación de instructor SSI n.º 000000 en vigor hasta 2027, recibidos por email el 12/10. Seguro RC pendiente de subir al panel».

No copies en la nota datos sensibles que no hagan falta: número completo del DNI, datos bancarios, fecha de nacimiento.

---

## 4. Señales de alarma

Con cualquiera de estas señales, no apruebes hasta aclararlo:

- El teléfono del registro no coincide con el público y, al llamar al público, nadie conoce a la persona.
- Email gratuito (gmail, outlook…) y web que no existe, está en construcción o es de otro centro.
- El nombre del centro coincide con uno conocido, pero la ciudad, la web o el email no.
- Documentos con nombres o NIF distintos del centro, editados, ilegibles o caducados.
- Seguro caducado, sin número de póliza o con una aseguradora que no existe.
- Presión para aprobar rápido o petición de aprobar «para probar».
- Varias solicitudes desde la misma persona o el mismo email con centros distintos.
- Stripe rechaza o restringe la cuenta conectada tras la aprobación.
- Ya existe otra cuenta gestora para el mismo centro: el servidor lo bloquea salvo confirmación expresa (`allow_second_manager`).

---

## 5. Rechazo

1. En *Administración → Verificaciones*, pulsa «Rechazar». Elige el método con el que comprobaste y escribe el motivo en la nota (por ejemplo: «el centro no conoce a esta persona»). El servidor no exige método ni nota para rechazar, pero ponlos siempre.
2. Lo que hace el servidor:
   - `center_claims.status='rejected'`;
   - la ficha borrador del centro queda oculta con `verification_status='rejected'`;
   - `users.requested_role` vuelve a `recreational`.
   - La cuenta sigue existiendo como buceador.
3. **El servidor no envía ningún correo al rechazar.** Escribe tú a la persona desde el buzón de contacto: rechazo, motivo general y cómo volver a solicitarlo con más documentación.
4. Si sospechas suplantación, avisa también al centro real por su teléfono o email público y apúntalo en el registro de incidencias. Si el intento afecta a datos personales, valora el procedimiento de brechas (`docs/legal/procedimiento-brechas.md`).
5. Para que vuelva a solicitarlo: hoy no hay botón para reabrir una solicitud rechazada. La persona puede pedir el alta de nuevo con otra cuenta, o la administración le asigna el rol a mano en *Administración → Usuarios* (`/api/admin/users/role`, con centro) tras verificarla igual que aquí. Esa vía no crea fila en `center_claims`, así que apunta la verificación en una nota aparte **[PENDIENTE TITULAR]**.

---

## 6. Qué pasa después de aprobar

Lo hace `/api/admin/center-claims/review` con `decision=approve`.

**Centro**

- La cuenta pasa a `role='center'` con `center_id` de su ficha.
- La ficha se publica (`active=1`, `verification_status='verified'`, `data_confidence='provider_verified'`).
- La persona queda como **propietaria** del equipo (`center_members.member_role='owner'`).

**Freelance**

- La cuenta pasa a `role='freelance'`, sin centro.

**En los dos casos**

- Se cierran todas sus sesiones (`DELETE FROM sessions`): al volver a entrar ya ve el panel.
- Recibe el correo `center_verified` («Tu perfil profesional está verificado»).
- **Empieza la prueba gratuita** (`start_trial()`): por defecto 60 días del plan Pro (`plans_trial_days`, `plans_trial_plan` en *Administración → Planes*). Solo una vez por prestador (`plan_trial_used`).
- Recibe avisos de renovación a 30, 7 y 1 días (`run_plan_jobs()`). Al terminar sin pagar, pasa a **ficha gratuita**: sin reservas online nuevas, con «Solicitar información», las reservas existentes se mantienen y la exportación sigue disponible.
- Aparece en el directorio público (`public_center_sql()` solo muestra centros verificados).

**Seguimiento recomendado tras aprobar**

- [ ] Primera semana: ha activado Stripe y Stripe ha verificado la cuenta.
- [ ] En 15 días: datos fiscales completos y certificado de seguro subido con su caducidad (*Administración → Planes*, columna de datos que faltan).
- [ ] Ha aceptado las condiciones para centros vigentes. Si se publica una versión nueva, la web se la pide al entrar (`legal_pending_for()`).
- [ ] Antes de que acabe la prueba: contacto comercial sobre el plan **[PENDIENTE TITULAR]**.

---

## 7. Modo piloto e invitaciones

- **Activar:** *Administración → Funciones → Modo piloto*. Con él activo, el registro profesional exige un código (`pro_signup_check()`).
- **Crear un código:** *Administración → Funciones → Invitaciones* (POST `/api/admin/invites`). Formato `WOD-XXXXXXXX`, con nota y caducidad (30 días por defecto, máximo 365).
- **Anular un código:** la misma ruta con `revoke`.
- La invitación **no sustituye a la verificación**: quien entra con código sigue pasando por la revisión de las secciones 2 a 6.

---

## 8. Puntos abiertos

- **[PENDIENTE ABOGADO]** Plazo de conservación de los documentos de verificación recibidos por email y base legal de ese tratamiento.
- **[PENDIENTE ABOGADO]** Licencias y seguro mínimos exigibles por país para aceptar un centro, y si WORLDIVES debe comprobarlos o basta la declaración del centro (`declares_licences`).
- **[PENDIENTE TITULAR]** Correo automático de rechazo (hoy no existe) y forma de reabrir una solicitud rechazada.
- **[PENDIENTE TITULAR]** Pantalla de administración con los datos fiscales y el certificado de seguro de cada centro (hoy solo hay CSV de DAC7 y descarga por URL).
- Corregir el texto de ayuda de *Administración → Verificaciones*, que todavía menciona la sugerencia por teléfono.
