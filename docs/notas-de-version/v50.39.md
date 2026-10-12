# WORLDIVES DISCOVERY v50.39: inicio de sesión y registro más sencillos (encargo 2, punto 7)

Primera entrega del encargo «6 mejoras de prioridad alta para centros». Las Fases 1 (seguridad, v50.31) y 1B (modos de reserva, v50.32) del encargo anterior ya estaban entregadas, como pide el encargo. El orden de las siguientes versiones:

- **v50.40:** manifiesto de salida y formularios firmados (puntos 1 y 5).
- **v50.41:** cancelar una salida por mal tiempo, cambio de fecha por el cliente y lista de espera (puntos 2, 3 y 4).
- **v50.42:** check-in sin conexión (punto 6) y entrega final del encargo.

## Qué había antes
- **El diseño de dos columnas de la v50.30 seguía en el código** (foto a la izquierda, formulario a la derecha), pero dos cosas lo recargaban:
  - **Campos que se veían sin deber verse.** El campo «Código de verificación o código de recuperación» aparecía siempre en el inicio de sesión, y los campos de centro (nombre, teléfono, ciudad, web, código de invitación y el aviso de verificación) aparecían siempre en el registro, también para un buceador. Llevaban el atributo `hidden`, pero el CSS de `.field` y `.form-grid` lo anulaba.
  - **Un registro largo para todos:** usuario, contraseña repetida, desplegable de tipo de cuenta, casilla de publicidad, etc.
- **En el móvil** la foto ocupaba la parte de arriba.
- **Capturas antes y después** en `docs/capturas/encargo2/punto7/`: `antes-*` es la v50.30 y `despues-*` esta versión, en ordenador y en móvil.

## Qué cambia
- **Diseño de la v50.30 recuperado:** dos columnas, foto a la izquierda y formulario a la derecha. En el móvil, solo el formulario.
- **Iniciar sesión:**
  - solo «Email», «Contraseña» y «Entrar»;
  - debajo, un enlace pequeño «¿Has olvidado tu contraseña?» que lleva a la pantalla de recuperación, que ya existía;
  - la cuenta se puede seguir escribiendo con el usuario antiguo, porque el servidor acepta las dos cosas.
- **Verificación en dos pasos en pantalla aparte (`#/verificacion`):**
  - si la cuenta la tiene activada (obligatoria para los administradores), después de la contraseña se pasa a una pantalla solo para el código;
  - la contraseña se guarda solo en la memoria de la página mientras se escribe el código, nunca en el navegador;
  - si se recarga, se vuelve a pedir.
- **Darse de alta:**
  - **Primero, tres tarjetas:** Buceador, Centro de buceo y Profesional. Al elegir una aparecen solo sus campos, con un enlace «Cambiar» para volver a las tarjetas.
  - **Buceador:** nombre, email, contraseña y la casilla de condiciones.
  - **Centro de buceo:** nombre del centro, persona de contacto, email, teléfono, país, ciudad, contraseña y la casilla con las condiciones para centros, más el mensaje «Revisaremos tu centro y te avisaremos por email». El centro queda pendiente de aprobación, como desde la Fase 1.
  - **Profesional:** nombre, email, teléfono, titulación (de la lista, o «Otra» con texto), contraseña y la casilla con las condiciones para centros. La titulación queda en la ficha y en la solicitud que revisa la administración.
  - **Ya no se piden:** el nombre de usuario (se crea a partir del email, sin repetir), la contraseña repetida, la web ni la casilla de publicidad. La publicidad se activa en «Mi cuenta» (casilla que ya existía). Perfil, tallas y datos fiscales se piden después, en «Mi cuenta» o en el panel.
- **Verificación del email:**
  - no forma parte del formulario: al registrarse se envía el enlace, como ya se hacía;
  - mientras no se verifica, la cabecera de la cuenta muestra un aviso discreto con «Reenviar»;
  - la tarjeta «Email · Sin verificar» de «Mi cuenta» sigue igual.
- **Corrección general:** un elemento con el atributo `hidden` ya no se ve en ninguna pantalla, sea cual sea su estilo.
- **Textos nuevos en los 10 idiomas.** La casilla de condiciones de los profesionales usa frases ya traducidas para que no queden fragmentos sueltos.

## Estado del punto 7

| Parte | Estado |
|---|---|
| Diseño de dos columnas de la versión anterior; en el móvil solo el formulario | Completado (el diseño estaba; se quita lo que lo recargaba y la foto en el móvil) |
| Iniciar sesión solo con email, contraseña y «Entrar»; enlace pequeño debajo | Completado |
| Recuperación de contraseña en pantalla aparte | Ya estaba (`#/recuperar`) |
| Verificación en dos pasos del administrador en pantalla aparte | Nuevo (`#/verificacion`) |
| Registro con tres tarjetas, campos por tipo y «Cambiar» | Nuevo |
| Centro pendiente de aprobación con «Revisaremos tu centro…» | Completado (la aprobación es de la Fase 1; se añaden el país y el mensaje) |
| Verificación del email por enlace y aviso discreto hasta verificar | Completado (el enlace ya se enviaba; el aviso en la cabecera es nuevo) |
| Textos en 10 idiomas | Completado |

## Pendiente de decisión
- **Casilla de comunicaciones comerciales:** sale del registro y queda solo en «Mi cuenta». Si quieres ofrecerla también al darse de alta, se añade como casilla opcional.
- **Usuario antiguo:** las cuentas creadas con nombre de usuario pueden seguir entrando con él aunque la etiqueta diga «Email». Si se quiere obligar a usar el email, se cambia en el servidor.

## Cómo se probó
- **`tests/test_e2_p7_auth.py`, 6 pruebas:**
  - alta de buceador solo con nombre, email y contraseña: usuario único creado a partir del email y enlace de verificación enviado;
  - datos erróneos: email no válido, contraseña corta, sin aceptar condiciones, email repetido;
  - centro con país y ciudad, pendiente de aprobación y oculto;
  - profesional con titulación de la lista o con texto, y rechazado sin ella;
  - nadie se convierte en administrador ni en centro al registrarse;
  - segundo paso como petición aparte (sin sesión hasta el código);
  - contraseña olvidada con la misma respuesta exista o no la cuenta.
- **`tests/e2e_auth.py`, 58/58 en navegador, en ordenador y en móvil:**
  - inicio de sesión con solo dos campos y el enlace debajo de «Entrar»;
  - foto solo en ordenador;
  - contraseña olvidada en otra pantalla;
  - segundo paso en `#/verificacion` y sesión iniciada con el código;
  - tres tarjetas, «Cambiar» a mitad del alta y campos de cada tipo;
  - alta real de buceador, centro y profesional;
  - aviso de email sin verificar con «Reenviar»;
  - los 10 idiomas sin ningún texto sin traducir y sin desbordamiento en el móvil.
- **Suite completa (153 pruebas) y recorrido de todas las pantallas** con los 5 roles sin errores. El recorrido destapó una carrera antigua en las listas de Centros y Puntos (error si se salía de la página mientras cargaba), ya corregida.
