# App móvil en 3 módulos · Tanda 0

Encargo «App móvil en 3 módulos (Buceador, Centro PRO y Freelance PRO) y APK de pruebas», recibido el 13/10/2026.

La Tanda 0 no programa pantallas. Entrega:
- el estudio de mercado;
- el inventario de paridad web → app;
- el prototipo navegable con todas las pantallas nuevas.

**Se para aquí hasta que el titular apruebe el prototipo.**

## Qué se entrega

| Entregable | Dónde |
|---|---|
| Estudio de mercado (apartado 1) | `docs/app/estudio-mercado.md` |
| Inventario de paridad de los tres roles (apartado 8) | `docs/app/paridad.md` |
| Prototipo navegable (apartado 2.3) | `docs/app/prototipo/` (abrir `index.html`) y el enlace privado https://claude.ai/artifact/5AFVY13mj48D7VVMA26vK8 (para enseñarlo hay que compartirlo desde su menú «Compartir») |
| Capturas de las pantallas en Clásico y Futurista, a 390 × 844 y 360 × 800, y una muestra en tamaño Enorme | Hojas de contactos en `docs/capturas/app-tanda-0/` y las 376 capturas sueltas en un zip aparte |
| Estas notas, la tabla de estado y las decisiones pendientes | este archivo |

**Sin zips nuevos de la web:** la Tanda 0 no cambia el código de la web ni del servidor, así que los zips vigentes
siguen siendo los de la v50.47. El prototipo no va dentro de los zips de la web (como la app de `app-movil/`).

## El prototipo

- **89 pantallas**:
  - entrada, variante de pruebas, ajustes y reportar fallo: 4;
  - visitante: 3;
  - buceador: 26;
  - Centro PRO: 41;
  - Freelance PRO: 15.
- **Se puede tocar:**
  - barras inferiores por módulo y selector de perfil;
  - mapa con hoja inferior de tres alturas (se arrastra y además tiene el botón «Ver lista / Ver mapa»), marcador con
    tarjeta sincronizada y «Buscar en esta zona»;
  - reserva rápida en una hoja con «Cambiar» en cada línea, y su confirmación;
  - agenda Mes, Semana (también en horizontal), Día y Recursos;
  - solicitudes con cuenta atrás, aceptar, rechazar con motivo y «Deshacer» durante 10 s;
  - escáner con lecturas simuladas (válida, usada, caducada, de otro centro, de otra salida, cámara denegada);
  - lista del barco, resumen para el barco, contar a bordo y cancelar avisando a todos;
  - WhatsApp con el mensaje ya escrito en el idioma del cliente;
  - el aviso push del freelance que abre la solicitud.
- **Controles del prototipo** (fuera del móvil): tema Clásico, Futurista o Automático; texto Normal, Grande o Enorme;
  ancho 390 o 360.
- **Notas al lado de cada pantalla:** qué enseña, qué usa de la web y qué falta hoy en el servidor (marcado
  «Pendiente»).
- **Datos:** de ejemplo, con los nombres del entorno de pruebas: Centro de Buceo Pruebas en Xàbia, barco Neptuno,
  Iván instructor, Bea Buzo, Tito Guía en Tulum.
- **Comprobado:**
  - 376 capturas sin errores de consola ni nada que se salga de la pantalla;
  - **contraste medido con axe-core** en las 178 combinaciones de pantalla y tema (89 pantallas × 2 temas): **0 fallos**. Había uno: el verde de
    WhatsApp tenía 4,3 : 1; ahora tiene 5,4 : 1.

### Cómo se ha aplicado la dirección visual (apartado 2)

- **Clásico (claro) por defecto para todos.** Futurista: azul Abismo con textos blancos y acentos turquesa, sin neón,
  brillos ni efectos de cristal.
- **Colores de la marca con las variables `--wd-*`**, las mismas que la web.
- **Estados con color, icono y texto:**
  - confirmada o pagado: verde con ✓;
  - pendiente de pago: naranja con reloj;
  - solicitud: azul con sobre;
  - cancelada: gris tachado;
  - urgente: rojo, solo para lo que caduca en menos de 3 h.
- **Inter**, 16 px de cuerpo, cifras grandes, pesos 400 a 600.
- **Iconos de trazo siempre con texto debajo.** Ningún botón importante es solo un icono. Sin emojis.
- **Motivos de buceo, con medida:**
  - bandera de buceo circular en los marcadores (la misma de la web);
  - curvas de batimetría muy suaves en cabeceras;
  - calendario coloreado como carta de profundidad (en Futurista, «más intenso = más lleno»);
  - plazas del barco dibujadas como asientos.
- **Indicadores circulares solo en tres sitios:** ocupación del día, cuenta atrás de solicitudes y próxima inmersión.
- **Para el barco:** botones de 56 px en check-in y «Subir a bordo». Nada depende solo de deslizar: siempre hay un
  botón.
- **Nada de lo prohibido:** carruseles automáticos, ventanas al abrir, publicidad, sonidos ni menú hamburguesa.

## Tabla de estado

| Punto del encargo | Estado | Nota |
|---|---|---|
| 1 · Estudio de mercado | **Completado** | Solo con resultados de búsqueda: desde aquí no se pudo abrir ninguna página. Sin capturas de las tiendas (la red de este entorno las bloquea). Corrige 18 cosas del resumen: FareHarbor sí gestiona barcos; DivePlanner Pro cuesta 29 €/mes o 24 €/mes en anual y cobra 3–5 %; Lueira también tiene 9 idiomas y no cobra comisión |
| 2.1–2.2 · Dirección visual | **Completado** en el prototipo | Ver arriba |
| 2.3 · Prototipo actualizado | **Nuevo** | El zip `worldives-app.zip` no llegó: el prototipo se ha hecho desde cero siguiendo el encargo. Si se envía, se une a este |
| 3 · Estructura (módulos, selector, barras, contadores) | **Nuevo** (prototipo) | |
| 4 · Módulo Buceador | **Nuevo** (prototipo) | Buddies no existe en la web |
| 5 · Módulo Centro PRO | **Nuevo** (prototipo) | Ver «Lo que falta en el servidor» |
| 6 · Módulo Freelance PRO | **Nuevo** (prototipo) | |
| 7 · WhatsApp manual | **Nuevo** (prototipo) | La web no tiene el botón por cliente con mensaje ya escrito. Los avisos automáticos (v50.47) **ya estaban** |
| 8 · Inventario de paridad | **Completado** | 219 funciones: buceador 69 (100 % en la app), centro 95 (9 «Disponible en la web»), freelance 55 (1 «Disponible en la web»: el plan) |
| 9 · APK de pruebas | Pantallas en el prototipo (entrada de pruebas y reportar fallo) | Se programa en la Tanda 1. Hoy existe la APK 0.1 de React Native con datos de ejemplo (ver la decisión 1) |
| 10 · Requisitos de las tandas siguientes | **Ya estaba** | Fase 1 (v50.31), Fase 1B (v50.32), barcos y manifiesto (v50.40), aislamiento entre centros (v50.47), motor por días (v50.44) |
| 11 · Pruebas | Visual y contraste del prototipo: **completado** | Las promesas se miden con la app de verdad (Tanda 4) |
| 13 · Pendiente de decisión | Ver abajo | |

## Lo que falta en el servidor (sale del inventario de paridad)

**No existe hoy:**
- Buddies (lista, «Mi código», grupos, «¿Buceamos?») y la marca «busca compañero».
- Estado del mar (decidido: boyas de Puertos del Estado, `docs/app-movil/02-datos-y-api.md`).
- Vista por recursos (barcos × instructores).
- Botón de WhatsApp por cliente con mensaje en su idioma.
- Push.
- Lista de sesiones abiertas.
- Unidades.
- Tamaño de texto y temas: la web tiene un solo tema.

**Existe en parte:**
- **Check-in con el QR de la reserva:** hoy el QR solo abre una página de consulta y la presencia se marca a mano en
  la lista del barco.
- **Mover a otra salida:** solo dentro del mismo servicio.
- **Manifiesto sin conexión:** solo hoy y mañana, y sin PDF.
- **Recuento a bordo:** solo «presentes».
- **iCal:** solo exportar.
- **Cursos de varios días:** solo como servicio «por días».
- **Borrar la cuenta:** solo los buceadores.

**Un fallo de la web, no de la app:** recepción y encargado ven la pestaña «Cobros y pagos», pero el servidor les
responde 403. Se arregla en la próxima versión de la web.

**Lo que se hace a la vez:** el encargo dice que si una tanda necesita algo de otro encargo, se hace a la vez. Así que:
- Buddies se programa en el servidor dentro de la Tanda 1;
- check-in por QR, recursos y mover entre servicios, dentro de la Tanda 2.

## Pendiente de decisión del titular

> **Decidido el 13/10 (después de esta entrega):** 1 → **Capacitor**; 2 → **3 idiomas** (español, inglés y francés)
> de momento; 3 → **`com.worldives.app`** y **`com.worldives.app.pruebas`**. Las demás se aplican como se recomienda
> aquí hasta que el titular diga otra cosa. Ver `docs/app/tanda-1.md`.

**Las dos primeras chocan con lo decidido el 13/10 y cambian el trabajo de las tandas siguientes.**

1. **Tecnología: ¿Capacitor o React Native?**
   - **El choque:**
     - Este encargo dice que sigue vigente Capacitor 8: la web cargada dentro de la app.
     - El 13/10 elegiste React Native + Expo, y la APK 0.1 está hecha así.
     - No pueden valer las dos.
   - **Recomiendo Capacitor**, por lo que pide este encargo:
     - paridad del 100 % con la web (219 funciones);
     - «la app no crea lógica nueva»;
     - las pantallas nuevas se programan una sola vez, en la web en modo app, y sirven también a quien usa la web en
       el móvil.
   - **Con React Native** habría que rehacer en la app las 219 funciones y mantener dos interfaces.
   - **Lo nativo** (escáner QR, push, Face ID, sin conexión) va con complementos de Capacitor.
   - **Qué pasa con la APK 0.1:**
     - queda como prototipo para las pruebas cronometradas;
     - la Tanda 1 sería la primera APK con Capacitor.
2. **Idiomas de la app: ¿9 o 3?**
   - El encargo pide 9 (con pruebas en alemán y polaco).
   - El 13/10 decidiste español, inglés y francés.
   - **Con Capacitor, los 9 salen gratis de la web.** Recomiendo 9 si eliges Capacitor.
3. **Nombre del paquete de Android.**
   - El encargo usa `com.worldives.app` (y `com.worldives.app.pruebas` para pruebas).
   - La APK 0.1 usa `com.worldivesdiscovery.app`.
   - Recomiendo los del encargo. Todavía no hay nada publicado, así que cambiarlo no cuesta nada.
4. **Roles del personal.**
   - El encargo dice «dueño y encargado: todo».
   - Hoy el encargado no puede devoluciones, Stripe, tarifas, escaparate, equipo ni plan, y tampoco guardar barcos.
   - El instructor ve todas las salidas, no solo las suyas.
   - ¿Se cambian las reglas del servidor a lo que dice el encargo?
5. **Borrar la cuenta de centros y freelance desde la app.**
   - Apple exige que se pueda borrar desde la app cualquier cuenta creada en ella.
   - Hoy centros y freelance tienen que escribir.
   - Propuesta: solicitud de baja desde la app, con plazo para resolver las reservas futuras.
6. **«Contar a bordo»** (13.1).
   - Recomiendo incluirlo en la Tanda 2: la web ya marca «Presente» y solo falta contar la subida y la vuelta al barco.
   - Es poco trabajo y ayuda a la seguridad.
7. **Nombre del tema oscuro** (13.2). Recomiendo «Noche»: es más sobrio que «Futurista».
8. **Tap to Pay de Stripe** (13.3).
   - Recomiendo estudiarlo para una versión futura.
   - España aparece en la lista de Stripe, pero hay que confirmarlo.
9. **Nombre en las tiendas** (13.4). Recomiendo una sola app «WORLDIVES» para todos.
10. **Fotos.**
    - El prototipo usa las fotos por defecto de la web, que siguen sin origen registrado
      (`docs/legal/imagenes-origen.md`).
    - Hay que cambiarlas por fotos con licencia antes de enseñarlo fuera del equipo.
11. **El zip `worldives-app.zip`** (prototipo y kit del modo app) no llegó con el encargo. Si existe, conviene
    enviarlo para unirlo a este prototipo.

## Para revisar el estudio de mercado

- Abrir las URL marcadas «verificado (búsqueda)» y confirmar los datos. Desde este entorno no se pudo.
- Hacer las capturas de las fichas de las tiendas desde un móvil o un ordenador normal (lista en el apartado 10 del
  estudio).
- Saber a qué «DiveOps» se refería el resumen: hay dos empresas con ese nombre.
