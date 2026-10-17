# Plan — Alta con correo: idioma correcto, un solo correo y aviso en la app (serie 45)

> **Normativo-vivo.** Pedido del dueño del 2026-10-17. Va **cuando la serie 43 esté en
> `master`** (#236–#239), porque comparte `i18n/*/common.json` y `useAppStore.ts` con ella, y
> **antes de la serie 44** (`PLAN_BACKOFFICE.md`): es pequeña y los probadores la notan en el
> primer minuto. No toca contenido (ADR-62) ni migraciones.
>
> El número de serie (45) es provisional y el ADR será el siguiente libre. La sesión que incorpore este plan
> los confirma con:
> - `grep -n '^### 4' docs/AUTONOMOUS_STATE.md | tail -1`
> - `grep -n '^## ADR-' docs/DECISIONS.md | tail -1`

## 1. Por qué

**Lo que pasó.** El dueño se registró desde un iPhone el 2026-10-17 a las 02:21:15 UTC. Los
logs de Railway muestran dos correos aceptados por Resend en el mismo segundo, **los dos en
inglés**:

- `Welcome to Whetzy, Prueba!`
- `Verify your Whetzy email`

**Lo esperado:** el correo llega en el idioma con el que el alumno se registró, la app le dice
que verifique y, al verificar, le lleva a donde corresponde.

Estado en `master` `2246cd2`, comprobado el 2026-10-17:

- **El backend ya respeta el idioma de la cuenta.** `register` (`endpoints/auth.py`) llama a
  `send_email_verification(..., lang=user.language)` y a `send_welcome(...)`. Las plantillas
  ES/EN están en `services/email.py`.
- **El fallo está en qué idioma se guarda:**
  - `AuthScreen.tsx:79` empieza en `'es'`, y `:136-139` lo cambia por el idioma del navegador.
    No mira `i18n.language`, que sí lee el `whetzy_lang` que el alumno eligió en la portada
    (`i18n.ts:23-37`).
  - La portada (`LandingScreen.tsx:30-35`) tampoco mira `whetzy_lang`, y su botón principal
    lleva a `/auth` sin `?lang` (`:147`).
  - Resultado: un iPhone en inglés con la portada en español registra la cuenta en inglés.
  - OAuth crea la cuenta sin idioma (`oauth.py:378-384`), así que queda el valor por defecto.
  - `AuthScreen.tsx:83-84` tiene dos errores de OAuth escritos en español, sin i18n.
- **La app nunca dice «verifica tu correo».**
  - En `frontend/src`, sin contar tests, ningún fichero usa `email_verified` (búsqueda de
    `email_verified|emailVerified`).
  - `UserRead` (`api.ts:289`) no trae ese campo, aunque `/auth/me` lo devuelve
    (`schemas/user.py:96`).
- **Reenviar el correo** solo se puede desde la página de enlace caducado.
  `POST /auth/resend-verification` es público, no revela si la cuenta existe y tiene el límite
  de ritmo de las rutas sensibles (`security_middleware.py:63-72`).
- **Tras verificar:**
  - `VerifyEmailPage` dice «Ir a iniciar sesión» y lleva a `/login`.
  - `/login` devuelve a la app si hay sesión (`useRedirectIfSignedIn`).
  - El enlace del correo no lleva idioma (`email.py:483`).
- **Lo que cambia hoy estar verificado:**
  - las recompensas por invitar (`economy.py:424`, `endpoints/economy.py:132`);
  - algunos correos periódicos (`periodic.py:150,230`).

  No bloquea nada más.

## 2. Decisiones

Las firma el dueño al fusionar el PR de este plan. Pasan a `DECISIONS.md` como un ADR nuevo, con el siguiente número libre.

| # | Decisión |
|---|---|
| E1 | **El idioma de la cuenta es el que ve el alumno al registrarse.** Orden: `?lang=`, luego `whetzy_lang`, luego el navegador. Vale para el formulario, la portada y OAuth. Después solo lo cambia el alumno en Yo, que ya hace `PATCH /auth/me {language}`. |
| E2 | **Al registrarse sale un solo correo: el de verificación.** La bienvenida sale **al verificar**, una sola vez. Con OAuth la cuenta llega verificada, así que su bienvenida sale al crearla. |
| E3 | **La app no se bloquea** por no verificar. Tras registrarse se entra al onboarding como hoy. |
| E4 | **Mientras no esté verificado, la app lo avisa** con una franja: «Te enviamos un enlace a fe***@gmail.com · Reenviar · ×».<br>- Va en el armazón de la app, no dentro de Hoy, para no chocar con la serie 43.<br>- «Reenviar» usa el endpoint público que ya existe, con el email de la cuenta, y espera 60 s entre reenvíos en el cliente.<br>- La × la oculta durante esa sesión del navegador. |
| E5 | **El enlace del correo lleva el idioma**: `/verify-email?token=…&lang=es\|en`.<br>- Al verificar se muestra «Email verificado».<br>- Con sesión abierta, «Continuar» lleva a `/` y refresca `/auth/me`, y la franja desaparece.<br>- Sin sesión, «Iniciar sesión» lleva a `/login?lang=…`. |
| E6 | Los errores de OAuth del formulario pasan a i18n ES/EN. |

## 3. Serie 45

Reglas para cada fila: una rama y un PR, test en rojo antes del cambio y en verde después, la
suite entera y el verificador §7.

| Fila | Qué | Ficheros clave | Tests (rojos hoy) |
|---|---|---|---|
| 45.1 (S) | E1 y E6: idioma del alta | `frontend/src/pages/AuthScreen.tsx`: el estado inicial sale de `?lang`, o si no de `i18n.language`; se quita la sustitución por el navegador.<br>`LandingScreen.tsx`: `resolveLandingLang` lee `whetzy_lang`; enlaces `/auth?lang=` y `/login?lang=`.<br>`backend/app/api/v1/endpoints/oauth.py`: `/start?lang=` guarda el idioma en una cookie corta junto al `state` (como `set_oauth_state_cookie` en `core/cookies.py`); el callback la usa **solo** al crear la cuenta.<br>i18n ES/EN. | vitest: con `whetzy_lang=es` y el navegador en `en`, el registro manda `language:'es'`; el botón de la portada lleva `?lang=`.<br>pytest: OAuth con `start?lang=en` crea la cuenta nueva con `language='en'`; una cuenta que ya existe no cambia; un `lang` no válido se ignora. |
| 45.2 (S) | E2: un solo correo | `endpoints/auth.py`: `register` deja de llamar a `send_welcome`; `verify_email` manda la bienvenida si la cuenta no estaba verificada.<br>`oauth.py`: bienvenida al crear la cuenta.<br>`services/email.py`: `verify_url` con `&lang=`. | pytest, con el envío capturado sustituyendo `email._dispatch`:<br>- registro en `es` → 1 correo, «Verifica tu email en Whetzy»;<br>- registro en `en` → 1 correo, «Verify your Whetzy email»;<br>- verificar → la bienvenida sale 1 vez;<br>- segundo intento con el mismo token → 400 y ningún correo. |
| 45.3 (M) | E4: franja «verifica tu correo» | `services/api.ts`: `UserRead.email_verified`.<br>`stores/useAppStore.ts`: `emailVerified` en `mapApiUser`.<br>`components/common/VerifyEmailBanner.tsx` y `.module.css` (nuevos; con tokens, sin estilos en línea), montados en `App.tsx` dentro de la app con sesión.<br>i18n ES/EN. | vitest:<br>- la franja aparece con `email_verified:false` y no con `true`;<br>- «Reenviar» llama a `resendVerification(email)` y se desactiva 60 s;<br>- la × la oculta durante la sesión;<br>- el email sale enmascarado.<br>e2e: tras el registro, la franja es visible. |
| 45.4 (S) | E5: página de verificación | `pages/VerifyEmailPage.tsx`: lee `lang`, muestra «Continuar» o «Iniciar sesión» y refresca `/auth/me`.<br>i18n: `verifyEmail.continue` pasa a «Continuar» y se añade `verifyEmail.login`. | vitest: con `lang=en` la página sale en inglés; con sesión, «Continuar» lleva a `/`; sin sesión, a `/login?lang=`.<br>e2e: registro → enlace del correo capturado en el backend de prueba → verificar → la franja desaparece. |

Documentación, en el mismo PR de cada fila:

- `docs/API.md`: OAuth con `?lang`; el registro ya no manda la bienvenida.
- `docs/MAPA_PRODUCTO.md`: la franja y la página de verificación.
- `docs/RUNBOOK.md`: qué hacer si «no me llega el correo»: «Reenviar» en la app y el panel de
  Resend.

## 4. Verificación de extremo a extremo

- `bash scripts/ci_local.sh` entero y `npx playwright test` sin rojos.
- Puerta de cierre de la serie, en verde en Chromium y en el proyecto `entre-sitios`: el e2e
  registro en español con el navegador en inglés → correo en español → franja visible →
  verificar → la franja desaparece.
- Tras cada fusión: `node scripts/check-deployed.mjs` (desde `frontend/`) en PASS.
- Prueba manual del dueño, con un iPhone en inglés:
  1. Pone la portada en «ES» y se registra.
  2. Llega **un** correo: «Verifica tu email en Whetzy».
  3. La app muestra la franja.
  4. Pulsa el enlace, luego «Continuar», y llega a Hoy sin franja.
  5. Llega la bienvenida, en español.
- Logs de Railway:
  - al registrarse, un solo `email_sent ... subject='Verifica tu email en Whetzy'`;
  - al verificar, `POST /auth/verify-email 200` y después el `email_sent` de la bienvenida.
