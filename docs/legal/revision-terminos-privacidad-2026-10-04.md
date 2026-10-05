---
title: "Revisión legal de Términos/Privacidad/Reembolsos publicados — Oleada 0.12 / D.8"
last_updated: "2026-10-04"
status: "DRAFT — propuestas para decisión del dueño (ADR-55); nada de esto se publica solo"
---

# Revisión legal de Términos/Privacidad/Reembolsos publicados

**No es asesoría legal definitiva.** Cada punto cita fuente oficial con fecha de lectura y dos
opciones con mi recomendación. Por **ADR-55**, lo único con efecto real es lo publicado en
`frontend/src/i18n/{es,en}/common.json` (claves `legal.*`); no cambio ese fichero en este PR —
eso exige decisión del dueño (`o se cambia el texto o el producto, nunca los dos a ciegas`).

Todas las líneas citadas son idénticas en `es/common.json` y `en/common.json` (mismo número de
línea en los dos ficheros, verificado).

---

## 1. «Licencia MIT» en los Términos — contradice el `LICENSE` real del repo

**Texto actual** (`frontend/src/i18n/{es,en}/common.json:686`, clave `termsP8`):
> ES: "El contenido educativo, algoritmos y diseño son propiedad de Whetzy. El código fuente de
> la plataforma está publicado bajo licencia MIT."
> EN: "The platform source code is published under the MIT licence."

**Problema.** El fichero `LICENSE` (raíz del repo, leído hoy) dice lo contrario:
> `LICENSE:5-9`: "The source code in this repository (backend/, frontend/, scripts/ and every
> other file that is not listed in section 2 or 3) is **proprietary. All rights reserved.** No
> licence is granted to use, copy, modify, distribute or sublicense it without prior written
> permission from the copyright holder."

Son afirmaciones opuestas sobre el mismo hecho (propietario vs. MIT) en dos documentos del
mismo repositorio. Un tercero que confíe en el Término publicado (MIT) podría alegar que tiene
derecho a copiar/redistribuir el código — justo lo que el `LICENSE` dice que no puede hacer.
Además, `LICENSE:15` cita `docs/legal/terms-of-service.en.md, section 3.1`, fichero que ya no
existe como texto vigente: se archivó el 2026-10-01 (`docs/archive/legal-borradores/`, ADR-55)
porque contradecía lo publicado. La referencia está rota.

**Fuente oficial:** ninguna — es un hecho interno (dos documentos del propio repo), verificado
leyendo `LICENSE` y `common.json` hoy, 2026-10-04. No aplica derecho externo.

**Opciones:**
- **A — Corregir el Término** (mi recomendación): sustituir la frase por algo que sí describe
  el código tal como está licenciado hoy, p. ej. ES: *"El contenido educativo, algoritmos y
  diseño son propiedad de Whetzy. El código fuente de la plataforma es propiedad de Whetzy; no
  se concede ninguna licencia de uso, copia o distribución salvo autorización expresa."* —
  coste: ninguno, un cambio de texto; riesgo: ninguno, reduce exposición.
- **B — Liberar de verdad parte del código bajo MIT** y que el Término sea cierto — coste: alto
  (decisión estratégica de qué se libera, posible impacto competitivo), fuera de lo que puede
  decidir un PR de texto.

**`LICENSE` está fuera de mi terreno** (ni `docs/legal/**`, ni `content/legal/**`, ni
`legal.json`) — lo señalo aquí y lo repito como `NECESITO` al final; su cita rota al fichero
archivado también hay que corregirla, y tampoco es mío tocarla.

---

## 2. «Exporta tus datos desde Perfil» — no existe ese botón hoy

**Texto actual** (`common.json:646`, clave `privacyL10`):
> ES: "Acceso, rectificación y portabilidad (exporta tus datos desde Perfil)"
> EN: "Access, rectification and portability (export your data from Profile)"

**Problema.** Verificado en el código, hoy:
- El endpoint existe: `backend/app/api/v1/endpoints/export.py:52` (`export_data`), y
  `backend/app/api/v1/endpoints/privacy.py:146` lo referencia como
  `data_export_url="/api/v1/export/data"`.
- **Nada en el frontend lo llama.** `grep -rn "export/data\|exportData\|downloadData" frontend/src`
  (excluyendo tests) → sin resultados. `ProfileScreen.tsx` no tiene ningún botón ni enlace de
  exportación — el único "export" que aparece ahí es la palabra clave de TypeScript
  (`export function ProfileScreen()`), no una función de producto.

Afirmar un botón que no existe es una afirmación de hecho verificable y falsa sobre el
producto, al margen de que el derecho de portabilidad (RGPD art. 20) en sí exista por otra vía
(email a `support@whetzy.com`, que sí está disponible).

**Fuente oficial:** RGPD art. 20 (derecho a la portabilidad) no exige que el mecanismo sea un
botón en la app — email también vale. El problema es la descripción inexacta del medio, no el
derecho en sí.

**Opciones:**
- **A — Cambiar el texto** (mi recomendación si no hay UI a corto plazo): *"Acceso,
  rectificación y portabilidad (escríbenos a support@whetzy.com)"* — coste: ninguno, ya
  funciona por email.
- **B — Pedir la UI a S1** (`NECESITO`): un botón en `ProfileScreen` que llame a
  `GET /api/v1/export/data` (el backend ya existe, falta solo el frontend) — coste: bajo
  (endpoint ya hecho), pero no es decisión mía ni tiempo que pueda comprometer por S1.

Dejo las dos; si el dueño prefiere la B, lo anoto como `NECESITO` a S1 en el resumen de cierre.

---

## 3. La cláusula de desistimiento concede y renuncia a la vez, y la sección de reembolsos la deja vacía

**Texto actual:**
- `common.json:678`, clave `termsP5withdrawal`:
  > ES: "Si resides en la UE, puedes desistir en 14 días (Directiva 2011/83/UE). Al iniciar el
  > servicio digital, aceptas renunciar al desistimiento. Contacta support@whetzy.com para
  > ejercerlo."
- `common.json:701`, clave `refundH3`: "3. Desistimiento en la UE" — **sin ningún párrafo
  debajo**: `frontend/src/pages/LegalScreen.tsx:143-146` renderiza
  `<h2>{t('legal.refundH3')}</h2>` seguido directamente de `<h2>{t('legal.refundH4')}</h2>`, sin
  un `<p>` entre medias. Un usuario que abra `/refund` ve el título "3. Desistimiento en la UE"
  sin ninguna explicación.
- En cambio, `common.json:708` (`checkout.euWithdrawalWaiver`, el texto real que se muestra y
  se acepta en el checkout) sí está bien formado: *"Acepto que el servicio digital se active de
  inmediato y reconozco que pierdo mi derecho de desistimiento de 14 días una vez que el
  contenido se suministre (Art. 16.m, Directiva 2011/83/UE)."*

**Problema.** `termsP5withdrawal` dice en la misma frase: (1) tienes 14 días para desistir, (2)
al empezar el servicio renuncias a ese derecho, y (3) contacta a soporte para "ejercerlo" — sin
decir qué es "lo" que se ejercería si ya se renunció. Es autocontradictorio tal como está
escrito, aunque el mecanismo legal real (art. 16.m, Directiva 2011/83/UE: el consumidor puede
renunciar expresamente al desistir de contenido digital una vez empieza la prestación, y
`checkout.euWithdrawalWaiver` lo redacta bien) sí es válido. El problema es solo de redacción
del Término, no del mecanismo de checkout. Y la sección "3. Desistimiento en la UE" del
`/refund` queda vacía — un hueco real en el texto publicado, no solo una contradicción.

**Fuente oficial:** Directiva 2011/83/UE, art. 16(m) (excepción al desistimiento para
contenido digital no suministrado en soporte material, cuando el consumidor consiente
expresamente y reconoce la pérdida del derecho) — texto consolidado en EUR-Lex
(`https://eur-lex.europa.eu/legal-content/ES/TXT/?uri=CELEX:32011L0083`), leído 2026-10-04.

**Opciones:**
- **A — Reescribir `termsP5withdrawal` para que remita al checkout, no se autocontradiga, y
  rellenar `refundH3`** (mi recomendación): ES propuesto para `termsP5withdrawal`: *"Si resides
  en la UE, el contenido digital se suministra de inmediato tras el pago. Al confirmarlo,
  renuncias a tu derecho de desistimiento de 14 días (Directiva 2011/83/UE, art. 16.m), como se
  te indica en el checkout."* — y un párrafo nuevo bajo `refundH3` (clave nueva `refundP3`) que
  explique lo mismo sin dejarlo en un titular vacío. Coste: ninguno, texto únicamente.
- **B — Dejarlo como aviso informativo genérico de "puedes tener derecho a desistir" sin
  mencionar la renuncia**, y gestionar cualquier reclamación caso por caso — más simple de
  redactar, pero no corrige la contradicción ni el hueco, y es más débil si Whetzy necesita
  invocar la renuncia frente a un usuario.

---

## 4. Procesadores no listados en `privacyProcessors`

**Texto actual** (`common.json:665`, clave `privacyProcessors`):
> "Para prestar el servicio, estos proveedores tratan datos por cuenta de Whetzy: Railway
> (servidores y base de datos), Cloudflare (la web y el correo entrante), Groq (…), Resend (…),
> Sentry (…) y Paddle (pagos en la web)."

**Problema, verificado uno por uno en el código:**
- **OAuth (Google, GitHub) — falta, y es real.** `backend/app/core/config.py:203-206` declara
  `GITHUB_CLIENT_ID/SECRET` y `GOOGLE_CLIENT_ID/SECRET`; `backend/app/api/v1/endpoints/oauth.py`
  los usa. Si un usuario entra con "Google" o "GitHub", esas empresas reciben la solicitud de
  autenticación y Whetzy recibe de vuelta el email/nombre del perfil — un flujo de datos real
  con un tercero que la política no nombra en absoluto.
- **Push (VAPID / Web Push) — ya razonablemente cubierto, no es una laguna nueva.**
  `docs/store/play-store-data-safety.md` ya lo describe como "enrutamiento vía el propio
  servicio de push del navegador del usuario" — el payload va cifrado extremo a extremo
  (protocolo Web Push) y el "tercero" es la infraestructura del propio navegador (FCM de Google
  para Chrome, autopush de Mozilla para Firefox), no un proveedor que Whetzy elige. Lo dejo
  anotado, prioridad baja, no como corrección urgente.
- **RevenueCat — correctamente ausente**, confirmado en `docs/legal/README.md`: sin apps en
  tiendas (17.14), no está activo; la propia política de ese fichero dice "se nombra el día que
  se encienda", criterio que sigo aquí.
- **Sentry, Groq, Cloudflare, Paddle — ya están**, confirmado línea por línea en `privacyProcessors`.

**Fuente oficial:** RGPD art. 13(1)(e) / 14(1)(e) — el responsable debe informar de los
destinatarios (o categorías de destinatarios) de los datos personales. Un proveedor de OAuth
que recibe la petición de autenticación y de vuelta entrega datos del perfil es un destinatario
real, no listarlo es una laguna de información, no solo de estilo.

**Opciones:**
- **A — Añadir Google y GitHub a `privacyProcessors`** (mi recomendación): ES propuesto, añadir
  al final: *"y, si entras con Google o GitHub, esos proveedores según su propia política de
  privacidad."* — coste: ninguno, texto únicamente.
- **B — Dejarlo implícito** bajo una frase general tipo "y los proveedores de inicio de sesión
  social que elijas" sin nombrarlos — más corto, pero menos preciso y más débil frente al
  estándar RGPD de informar "destinatarios" con especificidad razonable.

Nota aparte, no de texto: `CLAUDE.md` exige Sign in with Apple si existe cualquier OAuth antes
de enviar a tiendas (ADR-13, App Store 4.8) y hoy no hay `APPLE_CLIENT_ID` configurado — es un
hallazgo de producto/ingeniería, no de texto legal; lo dejo anotado para que quien lleve las
fichas de tienda (S6) o S1 lo tengan, no lo repito como opción de texto aquí.

---

## 5. «No se envían datos personales al proveedor de IA» — verificado contra el código, es más fuerte de lo que el código sostiene

**Texto actual** (`common.json:688`, clave `termsP9`):
> ES: "...No se envían datos personales al proveedor de IA."
> EN: "...No personal data is sent to the AI provider."

**Problema.** Leí `backend/app/services/ai/tutor.py` completo. `_get_weak_skills()`
(líneas 64-78) consulta `UserSkillState` del usuario concreto (`p_known < 0.4`) y
`explain_question()` (líneas 120-127) inyecta los nombres de esas habilidades débiles
**directamente en el `system_prompt`** que se manda a Groq (`provider.complete(...)`, verificado
que no hay ningún paso que lo filtre antes de la llamada). Es decir: el perfil de dificultad de
ESE usuario concreto sí sale hacia Groq, aunque — confirmado también — ni su nombre ni su email
ni ningún identificador directo acompañan la llamada (`backend/app/services/ai/provider.py`, sin
parámetro de usuario/metadata en la petición).

La propia política ya tiene la redacción correcta y más prudente, en la línea de al lado
(`privacyProcessors`, `common.json:665`): *"Groq (genera las explicaciones del tutor con IA a
partir del contenido de tu consulta, **sin tu nombre ni tu correo**)"*. `termsP9` dice algo más
fuerte ("ningún dato personal") que el propio código no sostiene con la misma seguridad: un
perfil de habilidades débiles de un usuario identificado internamente por Whetzy puede
calificar como "dato personal" bajo el RGPD (art. 4.1: "cualquier información sobre una persona
física identificada o identificable") desde la perspectiva del responsable (Whetzy), que sí
puede reidentificarlo — con independencia de que Groq, por su lado, no reciba el nombre.

**Fuente oficial:** RGPD art. 4(1) (definición de dato personal); doctrina del TJUE en
*Breyer v. Alemania* (C-582/14, 19-oct-2016) sobre que la identificabilidad se evalúa
considerando los medios razonablemente disponibles para **cualquiera** de las partes, no solo
el receptor — leído de resúmenes jurídicos especializados hoy, 2026-10-04, no de la sentencia
original (marcar como fuente secundaria, no primaria).

**Opciones:**
- **A — Alinear `termsP9` con la redacción ya prudente de `privacyProcessors`** (mi
  recomendación): ES propuesto: *"...Groq, nuestro proveedor de IA, recibe el contenido de tu
  consulta y tu perfil de habilidades, pero nunca tu nombre ni tu correo."* — coste: ninguno,
  texto únicamente, y es más defendible.
- **B — Dejar `termsP9` como está** y asumir el riesgo de que "ningún dato personal" se lea de
  forma amplia — no lo recomiendo: es la frase más fácil de contradecir con una sola consulta al
  código, y ya la contradice la propia política dos párrafos más abajo.

---

## 6. Edad mínima: 13 en el alta frente a 14 en España (y variación en otros países UE)

**Texto actual** (`common.json:672`, clave `termsP2`): "Debes tener al menos 13 años." El alta
real (`backend/app/models/user.py:117-118`, `backend/app/api/v1/endpoints/auth.py:72`) es
autocertificación de 13+ sin distinguir país.

**Problema.** Para España, el consentimiento del propio menor para el tratamiento de sus datos
exige **14 años**, no 13:
> BOE, Ley Orgánica 3/2018 (LOPDGDD), **artículo 7.1**, leído hoy 2026-10-04 en
> `https://www.boe.es/buscar/act.php?id=BOE-A-2018-16673`: *"El tratamiento de los datos
> personales de un menor de edad únicamente podrá fundarse en su consentimiento cuando sea
> mayor de catorce años."*

Esto choca con la base legal que la propia política declara (`privacyP3`: "ejecución de
contrato e interés legítimo", **no** consentimiento) — si la base no es el consentimiento, el
art. 7 LOPDGDD (que regula específicamente el consentimiento del menor) podría no aplicar
literalmente de la misma forma. Pero eso abre una pregunta distinta y más seria: la capacidad
de un menor de 13-14 años para **aceptar un contrato** (los Términos) bajo el Código Civil
español (arts. 1263 y ss.) — los menores no emancipados tienen capacidad contractual limitada,
con el contrato siendo anulable. No resuelvo esto yo: lo dejo como pregunta para el abogado.

**Además, 14 no es el único umbral distinto en la UE.** El art. 8(1) RGPD deja a cada Estado
fijar el umbral entre 13 y 16 años para el consentimiento digital. Verificado hoy (fuente
secundaria, agregador especializado, no texto oficial de cada país):
`https://gdprlocal.com/digital-age-of-consent-under-the-gdpr/` — Alemania, Países Bajos e
Irlanda: 16 años; Francia: 15 años; España: 14 años (confirmado arriba contra el BOE). El "13
años" global de Whetzy es el **mínimo absoluto** que permite el RGPD (art. 8.1, último inciso) y
por eso es insuficiente para varios de los mercados que el plan de distribución del #93
menciona como objetivo.

**Opciones:**
- **A — Subir el mínimo global a 16 años**, el techo del RGPD, sin distinguir país (mi
  recomendación si no hay apetito por lógica de alta distinta por país): simplifica el texto y
  la autocertificación a una sola regla, cubre todos los Estados miembro de golpe. Coste: pierde
  usuarios de 13-15 años en países donde sí bastaría 13-15; impacto en captación sin medir.
- **B — Alta con selector de país y mínimo por país** (13 EE. UU./general, 14 España, 15
  Francia, 16 Alemania/Países Bajos/Irlanda…): más preciso y no sacrifica usuarios donde la ley
  permite menos, pero es cambio de producto (formulario de registro + tabla de países), no solo
  de texto — lo marco también como `NECESITO` a S1 si el dueño elige B.

La pregunta de la capacidad contractual del menor (más allá del consentimiento RGPD) **no la
resuelvo aquí**: la dejo en el `NECESITO` final para el abogado, con las dos opciones anteriores
como punto de partida, no como respuesta completa.

---

## 7. Cookies `SameSite=None` sin banner — ¿exentas por ser de sesión?

**Texto actual** (`common.json:662`, clave `privacyCookies`): "Solo usamos cookies técnicas
necesarias. No se requiere banner de cookies."

**Verificado en código** (`backend/app/core/cookies.py`): las 4 cookies que el backend pone
(`whetzy_access`, `whetzy_refresh`, el flag `whetzy_logged_in` y `whetzy_mfa`, líneas 85-124)
son todas de autenticación — ninguna de analítica ni publicidad. Pero **ninguna es una cookie de
sesión en sentido estricto**: las tres primeras llevan `max_age` explícito (persisten tras
cerrar el navegador: `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS` en días, no
"hasta cerrar pestaña"); solo la de MFA es corta (5 minutos) pero tampoco es "hasta cerrar
sesión", es un `max_age` fijo. `SameSite=None` en sí (cuando el dominio del frontend y el de la
API no son el mismo sitio, `backend/app/core/cookies.py:40-61`) es un atributo de
compatibilidad de navegador, no cambia el análisis de consentimiento de cookies por sí mismo.

**Problema, con fuente oficial que sí distingue por duración, no solo por propósito:**
> AEPD (Agencia Española de Protección de Datos), *Guía sobre el uso de las cookies*,
> actualizada el 2023-07-11 (exigible desde 2024-01-11 tras seis meses de adaptación) — leída
> hoy 2026-10-04 vía fuentes que la resumen (`aepd.es/prensa-y-comunicacion/notas-de-prensa/...`,
> no descargué el PDF completo en esta sesión): la categoría de cookies técnicas exentas de
> consentimiento incluye **"cookies de autenticación o identificación de usuario (únicamente las
> de sesión)"** — la propia guía oficial califica la exención de autenticación con la coletilla
> "únicamente las de sesión", no cualquier cookie de autenticación sea cual sea su duración.

Las cookies de Whetzy son de autenticación (propósito exento) pero no son estrictamente "de
sesión" (duración). Esto no las convierte automáticamente en no-exentas — la doctrina más
amplia de "cookies técnicas o de seguridad" también cubre cookies de autenticación persistentes
en varias guías nacionales y en el dictamen GT29 04/2012 (que habla de necesidad para el
servicio solicitado, no solo de duración) — pero la redacción tajante "no se requiere banner"
se apoya en el argumento más débil (duración) en vez del más fuerte (propósito/necesidad), y
alguien que revise la guía de la AEPD literalmente podría objetarlo.

**Opciones:**
- **A — Mantener "no se requiere banner" pero cambiar el fundamento del texto**, de "son
  cookies de sesión" (no lo son) a "son estrictamente necesarias para el funcionamiento del
  servicio (autenticación), conforme al art. 5.3 Directiva 2002/58/CE y el dictamen GT29
  04/2012" (mi recomendación): no cambia nada del producto, corrige el fundamento jurídico sin
  tocar el resultado (sigue sin banner). Coste: ninguno.
- **B — Acortar la duración real de las cookies a sesión pura** (sin `max_age`, se borran al
  cerrar el navegador) para que la frase "cookies de sesión" sea literalmente cierta — esto es
  cambio de producto (afecta "recordarme" / tiempo de sesión del usuario, probablemente una
  regresión de experiencia que ya se corrigió por otro motivo — ver `cookies.py:3-13` sobre por
  qué `SameSite=None` existe) y no es decisión mía: lo marco `NECESITO` a S1/S5 si el dueño
  prefiere este camino en vez del A.

---

## Resumen de lo que no se puede resolver solo con texto (para el `NECESITO` del #89)

| # | Punto | Necesita además de texto |
|---|---|---|
| 1 | MIT vs `LICENSE` | corregir `LICENSE` (fuera de mi terreno) y su cita rota a `terms-of-service.en.md` archivado |
| 2 | Exportar datos | opción B: UI en `ProfileScreen` (S1) |
| 6 | Edad mínima | opción B: selector de país + mínimo por país (S1); pregunta de capacidad contractual del menor, sin resolver aquí |
| 7 | Cookies | opción B: acortar `max_age` a sesión pura (S1/S5) |

---

**Estado**: DRAFT — 7 propuestas con 2 opciones cada una, ninguna aplicada a `common.json`.
Pendiente de `NECESITO (dueño)` en el #89 y, donde aplique, de H.20 (revisión profesional).
