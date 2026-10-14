# Permisos de la administración (v50.54) · PENDIENTE DE ABOGADO

Fecha: 14/10/2026. Motivo: el punto 8 del encargo. La administración edita el contenido de la plataforma. Lo que
publican los centros y los freelance no lo modifica: solo lo modera. Tampoco debe ver datos privados innecesarios.

**En esta versión no se ha cambiado ningún texto publicado** (`app/legal/`). Lo que sigue son las preguntas para el
abogado y lo que hace la web hoy, comprobado con pruebas: `tests/test_v50_54_admin.py` y el recorrido
`tests/navegador/e2e_v50_54_moderacion.py`.

## 1. Qué datos personales puede ver la administración — PENDIENTE DE ABOGADO

**Lo que hace la web desde la v50.54:**

- **Casillas sin tocar el código.** En «Administración → Datos personales», seis casillas deciden qué puede abrir la
  administración. Cambiarlas no requiere tocar el código.
- **Cambiar una casilla pide un motivo.** El cambio queda registrado: quién, cuándo, qué casillas y por qué.
- **Cada acceso a datos personales queda registrado** en «Actividad», como «Acceso a datos personales», con quién,
  cuándo, qué dato, en qué pantalla y el motivo que escribió el administrador. Se registran:
  - las listas de reservas, de pagos, de correos y de cuentas, y cada reserva abierta;
  - las solicitudes de alta de centros, las propuestas de posición y las denuncias;
  - cada pantalla con casilla: descargos, fichas, documentos, clientes del centro, hojas de embarque y contenido de
    los correos.
- **Lo cerrado no llega al navegador.** El servidor no lo envía: lo oculta en origen, no en la pantalla.
  - Con «Nombre y email de quien reserva» cerrada, el nombre queda en nombre de pila e inicial («Marta L.») y el
    email no se envía.
  - Los teléfonos y las notas internas, cerrados, no se envían.
  - Una pantalla entera cerrada (descargos, ficha en PDF, documentos, clientes del centro, hoja de embarque) responde
    «La configuración de privacidad no permite a la administración ver…».

| Casilla | Para qué | Por defecto |
|---|---|---|
| Nombre y email de quien reserva | Atender incidencias de reservas y de pagos | Abierta |
| Teléfonos de clientes y contactos de emergencia | Solo si hay que llamar a un cliente por seguridad | Cerrada |
| Ficha del buceador y clientes de cada centro | Perfil, fecha de nacimiento, tallas, hoja de embarque y lista de clientes | Cerrada |
| Notas internas de los centros | Lo que el centro escribe para su equipo sobre una reserva | Cerrada |
| Formularios firmados, fichas de buceador y documentos | Descargos firmados, ficha en PDF y documentos que sube el buceador | Cerrada |
| Contenido de los correos enviados | Comprobar o reenviar un correo que no llegó | Abierta |

**Preguntas:**

1. **Minimización (RGPD art. 5.1.c).** ¿Qué casillas deben estar abiertas por defecto? Hoy solo están abiertas las dos
   que necesitan el soporte y los pagos.
2. **Base jurídica.** ¿Cuál es la base para que la plataforma acceda a datos que el buceador dio al centro? Por
   ejemplo: interés legítimo para resolver incidencias, o encargo del centro como responsable.
3. **Datos de salud.** ¿Deben quedar siempre cerrados para la administración los descargos firmados y la ficha
   médica, sin casilla?
4. **Política de privacidad.** ¿Hay que decir en ella que la plataforma puede acceder a estos datos, en qué casos y
   que cada acceso queda registrado? Texto propuesto:

   > **Acceso del equipo de WORLDIVES:** solo accedemos a los datos de una reserva (nombre y email de quien reserva)
   > para resolver incidencias de reservas y de pagos. A los demás datos que compartes con un centro (teléfono,
   > ficha de buceador, documentos firmados) solo accedemos cuando hace falta por seguridad o para atender una
   > petición tuya o del centro. Cada acceso queda registrado con quién, cuándo y por qué.

5. **Conservación del registro de accesos.** Hoy el registro de actividad se conserva 12 meses (configurable entre
   3 y 120 en «Administración → Legal»). ¿Es el plazo correcto?

## 2. Moderación del contenido de centros y freelance

**Lo que hace la web desde la v50.54:**

- **La administración no edita lo que publica un centro con titular o un freelance.** El servidor rechaza esos
  cambios (403). La administración solo puede ocultar con un motivo:
  - la ficha del centro;
  - el perfil del freelance;
  - un servicio;
  - una experiencia.
- **El titular recibe el aviso** en «Avisos» y por correo, en su idioma, con el motivo tal como lo escribió la
  administración.
- **El titular lo corrige y lo envía a revisión** con una nota. Mientras tanto no puede volver a publicarlo él solo.
- **La administración lo vuelve a publicar tal como estaba**, o lo mantiene oculto con otra nota que también recibe
  el titular.
- **Cada paso queda en «Actividad»** con quién, cuándo y por qué.

**Texto actual** (`app/legal/es/centros.md`): «Podemos restringir o suspender un perfil o un servicio si incumple
estas condiciones o la ley. Te informaremos **antes o en el momento** de la restricción, con los motivos, y podrás
responder.» La web ya cumple lo que dice ese texto.

**Preguntas:**

1. **Declaración de motivos (DSA art. 17).** El aviso lleva el motivo escrito por la administración. ¿Debe incluir
   también la norma o cláusula incumplida y cómo reclamar fuera de la plataforma? Si es así, se añade al correo y al
   aviso.
2. **Experiencias de un centro.** El texto actual dice «un perfil o un servicio». ¿Hay que nombrar también las
   experiencias y los viajes?

## Qué cambia cuando el abogado responda

Cuando el abogado responda:

- **Las casillas** se cambian desde la pantalla, sin tocar el código.
- **Los textos legales** que apruebe se traducen a los 8 idiomas y se publican como versión nueva de cada
  documento, como siempre.
