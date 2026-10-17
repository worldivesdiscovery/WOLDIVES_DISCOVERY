# WORLDIVES DISCOVERY v50.42: check-in en el barco sin cobertura (encargo 2, punto 6) y entrega del encargo 2

## Qué había antes
- **App instalable:** ya existía (`manifest.webmanifest` y `sw.js`). Funcionaba sin conexión solo para abrir la web; sin conexión no había ningún dato de reservas.
- **En el dispositivo** se guardaban solo preferencias (idioma, aviso de cookies…).
- **No había check-in de buceadores** en una salida, ni «no se presentó», ni notas por buceador.

## 6 · Check-in en el barco sin cobertura
- **«Check-in en el barco» (`#/barco`):**
  - se abre desde el planning (día de hoy o de mañana), desde el manifiesto de la salida o desde el acceso directo de la app instalada;
  - muestra las salidas del día con «Presentes 3/8»;
  - en cada salida, los buceadores por grupo con su nivel, Nitrox, alquiler, tallas, descargo firmado o no y contacto de emergencia (solo si lo han compartido).
- **Funciona sin conexión:**
  - al abrirlo con conexión, el manifiesto del día se guarda en el dispositivo;
  - sin cobertura, la app abre igualmente (también al recargarla) con los datos guardados y lo indica: «Sin conexión: usando los datos guardados».
  - «Preparar mañana» deja lista la salida del día siguiente la tarde antes.
- **Sin conexión se puede:** marcar «Presente» o «No se presentó» (con otro toque se desmarca) y escribir notas. Cada cambio queda «Pendiente de enviar».
- **Indicador discreto:** «Sin conexión · 3 cambios pendientes», abajo a la izquierda. Desaparece cuando todo está enviado.
- **Al recuperar la conexión, se sincroniza solo** (también al abrir la app):
  - el servidor compara campo a campo lo que vio el dispositivo con lo que tiene ahora;
  - si otra persona cambió lo mismo, aparece la pantalla **«Cambios en conflicto»**, con «En este dispositivo: …» y «En el servidor: … · quién», para elegir qué se queda;
  - el mismo valor en los dos sitios no es conflicto.
- **Privacidad en el dispositivo:**
  - solo se guardan las salidas de ese día (hoy o mañana) del centro;
  - nunca documentos;
  - al abrir la app se borran los días anteriores;
  - al cerrar sesión se borra todo; si quedan cambios sin enviar, se avisa antes.
- **Permisos:**
  - check-in: propietario, recepción e instructores (los instructores pueden marcar el check-in aunque su perfil sea de solo lectura);
  - otro centro o un buceador: nada (403).
- **Registro:** quién marcó a cada buceador, cuándo y si fue sin conexión (`checkin_by`, `checkin_source`). Cada envío queda en el historial de la salida.

## Migración `migrate_v50_42` (solo añade)
- **Columnas nuevas en `manifest_entries`:** `checkin_by`, `checkin_source`, `checkin_updated_at` y `note_updated_at`. Las de presente, «no se presentó» y nota ya estaban desde v50.40.

## Estado del punto 6

| Parte | Estado |
|---|---|
| La app instalable guarda el manifiesto del día para usarlo sin conexión | Completado (la app ya era instalable; los datos sin conexión son nuevos) |
| Check-in, presentes, «no se presentó» y notas sin conexión | Nuevo |
| Sincronización al recuperar la conexión y pantalla de conflictos | Nuevo |
| Indicador «Sin conexión · cambios pendientes» | Nuevo |
| Solo los datos de esa salida y sin documentos; se borran al terminar el día | Nuevo |

## Cómo se probó
- **`tests/test_e2_p6_offline.py`, 2 pruebas:**
  - el paquete del día solo trae hoy (y mañana bajo petición), nunca otros días ni documentos;
  - permisos de otro centro, de un buceador y de un instructor;
  - sincronización de presente, «no se presentó» y nota;
  - conflicto cuando recepción cambió lo mismo, sin conflicto si coincide el valor, y «mantener el mío»;
  - datos erróneos.
- **`tests/e2e_offline.py`, 13/13 en navegador (móvil):**
  - con conexión se guarda el día;
  - se corta la red y se recarga la app, que abre con los datos guardados;
  - se marcan dos estados y una nota, con el indicador «3 cambios pendientes» y nada enviado;
  - recepción cambia lo mismo; al volver la conexión aparece la pantalla de conflictos y se guarda;
  - la cola queda vacía y el indicador se oculta;
  - se borran los días anteriores, y todo al cerrar sesión;
  - sin errores ni desbordamiento.
- **Capturas** en `docs/capturas/encargo2/punto6/`.

## Entrega del encargo 2
Todo el resumen está en **`docs/entrega/entrega-encargo2.md`**: notas de cada versión, tabla de estado, pruebas (también las de permisos entre roles), capturas antes y después y lista de lo pendiente de decisión.
