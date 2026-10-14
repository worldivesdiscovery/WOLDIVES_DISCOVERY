# Cambios en los textos legales (v50.52) · para la revisión del abogado

Fecha: 14/10/2026. Motivo: el encargo de despliegue del titular (servidor Hostinger KVM 2 en la UE, registros externos
en Better Stack región UE, verificación en dos pasos obligatoria con cobros online y dominio
`worldivesdiscovery.com`). Los textos **no se publican** hasta que el abogado los revise.

**Comprobación previa (pedida en el encargo):** ningún texto menciona la comisión del 10 %. Se buscó «comisión»,
«commission», «10 %» y sus equivalentes en los 9 idiomas de `app/legal/` y en `docs/legal/`: solo aparecen frases que
dicen que **no** hay comisión por las reservas (el modelo es solo la cuota anual) y las comisiones de Stripe, que paga
la cuenta del centro. La prueba `test_no_commission_in_legal_texts_and_settings` lo vigila en cada versión.

## Lo que ha cambiado

| Documento | Dónde | Qué cambia |
|---|---|---|
| **Política de privacidad** (9 idiomas) | `app/legal/<idioma>/privacidad.md` · `#/legal/privacidad` | §4: el alojamiento nombra la **ubicación real del servidor** (campo nuevo `{{hosting_location}}`, en la UE); nuevo destinatario **copias de seguridad** (cifradas, campo nuevo `{{backup_provider}}`, UE); nuevo encargado **Better Stack** (sede en Praga, región de datos Europa) con qué recibe y para qué. §5: registros de seguridad y de accesos **14 días en el servidor y 30 días en Better Stack**; plazos de las **copias** (48 h / 30 días / 12 meses). §7: verificación en dos pasos obligatoria también con cobros online, antivirus de documentos y registros fuera del servidor |
| **Condiciones para centros y profesionales** (9 idiomas) | `app/legal/<idioma>/centros.md` §6 · `#/legal/condiciones-centros` | Nuevo punto: **la verificación en dos pasos es obligatoria al activar los cobros online**, también para quien del equipo tenga el permiso «Cobros»; 14 días para quien ya cobraba; sin ella solo «Mi cuenta»; los pagos de los clientes siguen funcionando; no se puede desactivar con cobros |
| **Anexo de encargado del tratamiento** (aún no publicado; borrador) | `docs/legal/anexo-encargado-tratamiento.md` §7 y §8 | Lista de subencargados al día: Hostinger (servidor, UE), Better Stack (registros, UE), proveedor de correo (pendiente de decisión), destino de las copias (pendiente de decisión, UE, cifradas), Stripe (si hay cobros), Meta/WhatsApp y Firebase (solo si se activan). **Aviso a los centros 15 días antes** de añadir o cambiar un subencargado, con derecho de oposición. Medidas de seguridad: remite al **informe ASVS 5.0 nivel 2** (`docs/auditoria/v50.51/asvs-5.0-nivel2.md`) y menciona la verificación en dos pasos obligatoria con cobros |
| **Registro de actividades de tratamiento** | `docs/legal/registro-actividades-tratamiento.md` | Nuevo destinatario **LOGS** (Better Stack, UE); actividad 15 (seguridad y registros) con lo que se envía y los plazos (14 / 30 días); actividad 16 (copias) cifradas en origen y con restauración de prueba mensual; HOST con la ubicación |
| **Procedimiento de brechas (AEPD 72 h)** | `docs/legal/procedimiento-brechas.md` §2 y paso 2 | Las **alertas llegan desde Better Stack** por correo **al titular, que es quien las atiende** (y avisa al técnico); exportar los registros de Better Stack como prueba. Pendiente del titular: segundo destinatario |
| **Aviso legal** | `app/legal/es/aviso-legal.md` | Sin cambios de texto: los datos de la SL (razón social, CIF, domicilio, registro) salen de *Administración → Legal* y hoy se ven como «[pendiente de completar]». Se rellenan en cuanto la SL esté constituida |
| *Administración → Legal* (campos) | `LEGAL_FIELDS` en `app/server.py` | Dos campos nuevos: **Ubicación del servidor** y **Copias de seguridad fuera del servidor**. Hasta que se rellenen, los textos dicen «[pendiente de completar]» (nunca se inventa un dato) |

Cómo se publican: al instalar la v50.52, cada texto cambiado se convierte en una **versión nueva** del documento (los
cambios de las condiciones para centros con **15 días de preaviso**, como siempre) y se pide aceptarla al entrar. Si la
administración ya hubiera editado un documento en la web, su versión manda y estos cambios hay que copiarlos a mano.

**Traducciones.** Los cambios están en los 9 idiomas: castellano (referencia), inglés (oficial) y, traducidos, francés,
alemán, italiano, portugués, polaco, neerlandés y chino (las traducciones indican que prevalece el castellano). Si el
abogado cambia el texto, hay que volver a traducir esos párrafos: la prueba `test_phase8_languages` avisa si una
traducción se queda sin un apartado, un marcador o una fila de tabla.

## Preguntas para el abogado

1. **Better Stack.** Confirmar la entidad que firma el contrato de encargo (DPA), su lista de subencargados y si hay
   transferencias fuera del EEE (soporte, copias) aunque los datos se alojen en la región de Europa. Los registros
   llevan la IP recortada o en forma de huella y el número interno de usuario: ¿se tratan como datos personales
   seudonimizados (entendemos que sí) y basta el interés legítimo (seguridad, art. 6.1.f y art. 32 RGPD)?
2. **Hostinger.** Confirmar la entidad contratante y su DPA (se ve en el contrato de hPanel), y redactar el campo
   «Proveedor de alojamiento» con esa razón social.
3. **Plazo de 30 días en Better Stack** frente a los 14 días del servidor: ¿es proporcionado para detectar e investigar
   incidentes? ¿Hay que reflejarlo en algún otro sitio (cookies, información en el registro)?
4. **Aviso de subencargados nuevos: 15 días** y efecto de la oposición del centro (terminar el encargo y exportar sus
   datos): ¿suficiente?
5. **Verificación en dos pasos obligatoria con cobros.** Es un cambio de las condiciones para centros: entra en vigor
   con 15 días de preaviso. El plazo técnico de 14 días para quien ya cobraba empieza cuando el servidor lo detecta;
   en el piloto no hay centros previos con cobros, así que no coinciden en la práctica, pero conviene confirmar la
   redacción y el orden (primero el aviso legal, luego el plazo técnico).
6. **Copias de seguridad:** destino externo en la UE **pendiente de decisión** del titular. ¿Debe nombrarse el
   proveedor concreto en la política de privacidad o basta «proveedor de almacenamiento en la UE» con la lista
   disponible a petición?
7. Lo que ya estaba pendiente sigue igual (forma de aceptación del anexo, papel de Stripe, transferencias a centros
   fuera del EEE…): `docs/legal/preguntas-abogado.md`.
