# Capturas — 46.10, la opción reacciona y el «+XP» vuela

Evidencia del PR de la fila 46.10 (`docs/PLAN_UI_AVANZADA.md` §7.3).

**Cómo se hicieron:** 2026-10-20, Playwright (Chromium) contra el stack local: Postgres 16 + Redis, backend en `:8000`,
Vite en `:5199`. Una cuenta nueva en cada captura y la pregunta `q010101001` forzada como en
`e2e/accessibility.spec.ts`. Spec: `frontend/e2e/quiz-reaccion.spec.ts`.

- **`acierto-{es,en}-{390,1280}.png`** (a 180 ms de responder `_my_var`): la opción correcta late (escala 1,04,
  300 ms) y el «+15 XP» ya ha salido de la tarjeta y está en el marcador. axe (WCAG 2.2 AA): 0 violaciones en las
  cuatro.
- **`fallo-es-{390,1280}.png`** (a 150 ms de responder `2var`): la elegida tiembla (±6 px, 300 ms) y la correcta late
  para que se vea cuál era.

**Fallo encontrado en la primera captura y corregido en este PR.** Al reaccionar, las opciones se desvanecían:
framer devolvía `opacity` al `initial` (oculto) en toda opción cuya variante nueva no la nombraba, y la elegida mal
desaparecía y dejaba un hueco. Ahora el e2e exige `opacity: 1` en las cuatro opciones; antes del arreglo lo vio en
rojo (`Received: "0"`).

**Ajenos a este PR, vistos en las capturas:**
- el toast «Incorrecto» se monta encima del aviso de verificar el correo;
- con la pregunta forzada (`force_question_id`, solo en tests) sale la clave sin traducir `quiz.reason.forced`.
