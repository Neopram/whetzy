# Lanzamiento piloto — kit del dueño (2026-10-01)

Para enseñar `whetzy.com` a 20–50 personas reales, escuchar qué les frena y convertir eso en
el siguiente backlog. Viene de `CIERRE_2026-09-30.md` §2.6 («usuarios antes que tiendas y que
catálogo») y §5.2, y de la fila 31.8 del ledger. No añadía analítica nueva por el veto de 31.5,
que el dueño levantó el 2026-10-20 (ADR-68).

Etiquetas: **[V]** comprobado en código o en vivo el 2026-10-01 · **[P]** inferencia fuerte,
sin probar contra producción.

## 0. Antes de enviar nada

1. **Fusiona los PRs del lanzamiento** (ya fusionados), que arreglan lo que vería un piloto en su primera
   sesión (recorrido de alta en local, ES y EN, 2026-10-01):
   - #45: CI en verde. Sin él, el resto sale en rojo.
   - #46: 11 rutas mostraban el nombre del icono en texto («cloud Microsoft Azure»).
   - #47: la primera sesión repetía preguntas.
   - #48: el primer «ESTUDIAR AHORA» decía «Sin preguntas disponibles».
   - #49: botón «Enviar comentario» en Perfil.
2. **Elige la dirección de correo** que vas a leer y ponla en `frontend/.env.production` como
   `VITE_FEEDBACK_EMAIL=…`. Sin ella el botón de #49 no aparece [V: `ProfileScreen.tsx`].
3. **Apunta el recuento base de usuarios** el mismo día que invitas (§4): hoy la base incluye
   tu cuenta y las de pruebas automáticas, que no son pilotos.

## 1. Invitación (para 20–50 personas)

Mándala uno a uno o en un grupo pequeño donde conozcas a la gente: estudiantes de
programación, gente preparando una certificación, compañeros que estén cambiando de carrera.

**Español**

> Hola, estoy probando **Whetzy** (whetzy.com), una app gratuita para aprender Python, SQL,
> IA o ciberseguridad con lecciones cortas y preguntas que se ajustan a lo que ya sabes. Puedes
> ejecutar el código en el propio navegador.
>
> ¿Me ayudas? Úsala **3 días, 10–15 minutos al día**, y el cuarto día te hago 5 preguntas
> rápidas. Si algo te frena o se rompe, dímelo con el botón «Enviar comentario» de tu Perfil o
> respondiendo a este mensaje. Gracias 🙏

**English**

> Hi! I'm testing **Whetzy** (whetzy.com), a free app to learn Python, SQL, AI or
> cybersecurity through short lessons and questions that adapt to what you already know. You
> can run the code right in your browser.
>
> Could you help? Use it for **3 days, 10–15 minutes a day**, and on day 4 I'll ask you 5 quick
> questions. If anything slows you down or breaks, tell me with the "Send feedback" button in
> your Profile, or just reply to this message. Thanks 🙏

## 2. Qué pedirles

- **3 días seguidos, 10–15 min al día.** Con eso basta para ver si vuelven y si la racha y
  los repasos tienen sentido.
- **Que empiecen sin ayuda**: crear cuenta → onboarding → «ESTUDIAR AHORA». No les expliques
  la app: lo que hay que ver es si se entiende sola.
- **Qué mirar** (díselo así):
  - ¿Supiste qué hacer al entrar?
  - ¿Las lecciones se entienden y las preguntas encajan con lo que acabas de leer?
  - ¿Alguna pregunta era imposible, repetida o en el idioma equivocado?
  - ¿Algo se rompió, tardó o no respondía?
  - ¿Volverías mañana sin que te lo recuerde?

## 3. Las 5 preguntas del día 4

En una conversación corta (llamada o mensaje), mejor que en un formulario. Apunta las
respuestas literales, no tu resumen.

1. **¿Qué te frenó?** El momento en que dudaste, te aburriste o lo dejaste.
2. **¿Qué volverías a usar?** Lo que te sirvió de verdad.
3. **¿Qué pagarías, y cuánto?** Si nada, por qué no.
4. **¿Qué te faltó?** Un tema, una función, una explicación.
5. **¿A quién se lo recomendarías?** Un nombre o un perfil concreto. Si no se te ocurre nadie,
   ya es una respuesta.

## 4. Cómo contar los registros reales sin analítica nueva

**Vía principal: endpoint que ya existe, de solo lectura.**

1. Inicia sesión en `whetzy.com` con tu cuenta de dueño.
2. En el mismo navegador abre
   `https://api.whetzy.com/api/v1/admin/metrics/funnel`.
3. Lee `total_users`: es el número de cuentas de la tabla `users`.

Por qué funciona:
- `GET /admin/metrics/funnel` cuenta `User.id` sin filtro (`backend/app/api/v1/endpoints/admin.py:93-143`) [V].
- Solo responde a una cuenta con rol `owner`; el rol `admin` ya no abre nada (`admin.py:31-37`) [V].
- La API acepta la cookie de sesión además del token (`backend/app/core/security.py:177-180`) [V].
- Que la cookie viaje al abrir la URL directamente no lo he probado en producción [P]. Si da
  `401`, inicia sesión otra vez en `whetzy.com` y repite.

**Pilotos reales = `total_users` hoy − el recuento base del día de las invitaciones.** Si
alguien de pruebas se registra entretanto, réstalo a mano.

**No uses la tarjeta «Total usuarios» del panel de admin**: sale siempre vacía [V]. La
pestaña Métricas pide `/admin/metrics/users` (`frontend/src/pages/AdminScreen.tsx:52`), que no
devuelve `total_users`. Está en la lista del dueño; no se arregla aquí por el veto de 31.5.

**Vía alternativa: los logs HTTP de Railway** (panel → proyecto `whetzy` → servicio `api` →
logs HTTP). Cada `POST /api/v1/auth/register` con estado `201` es un registro
(`auth.py:93` responde `201 Created`) [V], con su IP. Descarta la tuya. La retención visible
de esos logs es de unos 7 días (`CIERRE_2026-09-30.md` §1.1) [P].

## 5. Cuándo volver a llamar a una sesión

- **Si algo se rompe para un piloto**: en cuanto lo sepas, con el fallo concreto (qué hizo,
  qué vio, captura si la hay). Una sesión, un fallo, un PR pequeño.
- **Tras las conversaciones del día 4**: con la lista de lo que te dijeron, literal, y cuántas
  personas dijeron cada cosa. Ese es el siguiente backlog. Nada de catálogo ni de tiendas
  antes de eso.

Prompt para esa sesión (mismo formato que `CIERRE_2026-09-30.md` §6):

```
Lee CLAUDE.md y docs/LANZAMIENTO_PILOTO.md. Piloto con <N> personas, día <D>.
Lo que rompieron o pidieron, literal y con cuántas personas lo dijeron:
<lista>
Tarea: ordénalo por cuántos pilotos frena, propón un PR pequeño por punto (≤ ~500 líneas,
test en rojo antes) y haz solo los <K> primeros. Reglas: rama nueva desde master, nunca push
a master ni fusionar (ADR-45), sin analítica nueva (31.5). Informe con [Verified]/[Likely]/
[Guessing] y qué debe comprobar otra sesión antes de que yo fusione. Luego para.
```
