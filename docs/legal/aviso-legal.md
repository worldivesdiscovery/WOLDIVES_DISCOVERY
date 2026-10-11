# Ficha de revisión: Aviso legal

Versión v50.38 · 11/10/2026
Estado: borrador para revisión

## Texto publicado

- Castellano (referencia): `app/legal/es/aviso-legal.md`. Inglés (oficial): `app/legal/en/aviso-legal.md`.
- Ruta pública: `#/legal/aviso-legal`. Enlazado desde el pie de todas las páginas (`public/index.html`, `.footer-legal`).
- Es la primera versión (`LEGAL_VERSION = '2026-10-11'`). Las versiones nuevas se publican desde *Administración → Legal* con `legal_publish()` y quedan en la tabla `legal_documents` con su historial (`/api/legal/history`).
- No necesita aceptación: no está en `LEGAL_ACCEPTANCE`.

Esta ficha no repite el texto. Resume cada cláusula, indica en qué parte del código se apoya y lista lo que falta revisar.

## Datos del titular (LSSI-CE art. 10)

Los datos no están escritos en el texto. Son marcadores que se rellenan con *Administración → Legal* (`LEGAL_FIELDS`, guardados en `site_settings` con prefijo `legal_`, ruta `POST /api/admin/legal`; relleno con `legal_fill()`).

| Dato que exige el art. 10 LSSI-CE | Marcador | Campo en Administración | Estado |
|---|---|---|---|
| Nombre o razón social | `{{owner_name}}` | Titular | [pendiente de completar] |
| NIF | `{{nif}}` | NIF / CIF | [pendiente de completar] |
| Domicilio | `{{address}}` | Domicilio | [pendiente de completar] |
| Email de contacto directo | `{{email}}` | Email de contacto (se valida el formato) | [pendiente de completar] |
| Teléfono (no obligatorio, recomendable) | `{{phone}}` | Teléfono | [pendiente de completar] |
| Datos registrales (si es sociedad) | `{{registry}}` | Datos registrales | [pendiente de completar] |
| Nombre comercial y web | `{{trade_name}}`, `{{site_url}}` | Nombre comercial; `WOD_PUBLIC_URL` | Por defecto «WORLDIVES DISCOVERY» |

Si un campo está vacío, la web muestra «[pendiente de completar]» (`legal_fill()`), en inglés «[to be completed]».

**Pie de página.** `footerOwner()` en `public/assets/js/world-dives-v8.js` lee `/api/legal/info` (devuelve `owner_name`, `trade_name`, `nif`, `address`, `email`, `phone`) y escribe «© año · nombre comercial · titular · NIF · domicilio · email». Mientras no haya ningún dato, el pie solo dice «© WORLDIVES DISCOVERY» (`public/index.html`, `#footer-owner`). El pie **no** muestra el teléfono ni los datos registrales: están en el aviso legal, que se enlaza desde el pie. Es suficiente si el aviso legal es accesible de forma «permanente, fácil, directa y gratuita».

## Cláusulas

| # | Qué dice | Dónde se apoya en el código |
|---|---|---|
| 1. Titular | Datos del art. 10 LSSI-CE. | Ver tabla anterior. |
| 2. Objeto | Plataforma para buscar puntos, conocer centros y reservar y pagar actividades. WORLDIVES es **intermediario**; el centro presta la actividad y responde de ella. Remite a condiciones de uso y de reserva. | Decisión del titular nº 1. La reserva muestra «Prestado por…» (justificante `GET /api/bookings/<id>/receipt.pdf`, `app/wod/pdf.py`, prueba `test_voucher_names_the_provider_and_is_not_an_invoice`). Los cobros van a la cuenta Stripe del centro (`stripe_controller()`, `test_direct_charge_without_commission`). |
| 3. Propiedad intelectual | Diseño, código, textos, marca: del titular o con licencia. Contenido de centros y usuarios: de sus autores, con licencia gratuita y no exclusiva a WORLDIVES mientras esté publicado. Cartografía OSM (ODbL), satélite Esri, relieve GEBCO. Prohibido el *scraping*. | Atribuciones en `OSM_ATTRIBUTION`, `SAT_ATTRIBUTION`, `GEBCO_ATTRIBUTION` (`app/server.py`, bloque de mapas, `/api/map/config`). Créditos en `#/legal/creditos`. Origen de imágenes en *Administración → Medios* (`image_origins`, `docs/legal/imagenes-origen.md`). Descripciones de puntos reescritas (`app/wod/pointtext.py`, `docs/legal/catalogo-origen.md`). Contra el *scraping* solo hay límites de peticiones por IP (`app/wod/security.py`), no un bloqueo específico. |
| 4. Responsabilidad | Datos de puntos orientativos; datos del centro, responsabilidad del centro; sin garantía de funcionamiento continuo; enlaces externos sin control. | Página `#/legal/seguridad`. Avisos en la ficha de punto (`world-dives-v8.js`, nivel recomendado «La ficha no sustituye los requisitos del operador»). |
| 5. Contenidos ilegales | Se denuncian en `#/legal/denuncias`; se revisan y se retira lo ilegal. | `POST /api/reports` (tabla `content_reports`, límite por IP, aviso a administradores), `POST /api/admin/reports/resolve` (aviso a denunciante y afectado). Pruebas `test_report_review_and_decision_to_both_parties`, `test_reports_on_centre_point_photo`. |
| 6. Ley y jurisdicción | Ley española; el consumidor puede acudir a los juzgados de su domicilio. | Sin soporte técnico necesario. |
| 7. Contacto | `{{email}}`. | `LEGAL_FIELDS['email']`. Página `#/legal/contacto`. |

## Desajustes entre el texto y el código

1. **Mapa base.** El texto cita OpenStreetMap, Esri y GEBCO. El mapa base de producción es Protomaps propio con datos de OSM (`OSM_ATTRIBUTION` ya nombra a Protomaps). Conviene citar también Protomaps en la cláusula 3 para que coincida con la atribución del mapa.
2. **Scraping.** El texto lo prohíbe, pero no existe `public/robots.txt` (el servidor lo serviría, `PUBLIC_ROOT_FILES`) ni otra medida técnica; solo los límites de peticiones. No es un error, pero la prohibición se apoya solo en el contrato.
3. Nada más: el resto del texto coincide con el código.

## Puntos para el abogado y el titular

- **[PENDIENTE TITULAR]** Rellenar todos los campos de *Administración → Legal* antes de abrir la web. Hoy, en una instalación nueva, el aviso legal muestra «[pendiente de completar]».
- **[PENDIENTE ABOGADO]** Confirmar que el aviso legal cumple el art. 10 LSSI-CE: si la actividad necesita autorización administrativa o colegiación (no parece), y si hace falta indicar el número de IVA intracomunitario.
- **[PENDIENTE ABOGADO]** Confirmar que basta con mostrar en el pie titular, NIF, domicilio y email (sin teléfono ni registro), con enlace al aviso legal completo.
- **[PENDIENTE ABOGADO]** Licencia de los contenidos de centros y usuarios (cláusula 3): alcance («mientras sigan publicados») y si cubre las traducciones automáticas y la banda «Centros asociados» (esta última ya pide consentimiento propio, `logo_consent`).
- **[PENDIENTE ABOGADO]** Marca «WORLDIVES DISCOVERY»: comprobar el registro en la OEPM/EUIPO antes de afirmar que es del titular.
