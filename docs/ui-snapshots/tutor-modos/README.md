# Capturas: tutor por modos (ola 2)

Evidencia del PR del tutor por modos (2026-10-21). Decisión del dueño: «A fondo» solo en Pro Max.

**Cómo se capturaron.** `e2e/tutor-modos.spec.ts`, Playwright (Chromium) contra `vite` y el backend
local, en ES a 390 y a 1280 px. Registro, sesión y preguntas son reales. Dos cosas van simuladas en
la red, porque en local no hay pagos ni clave del LLM:
- el plan, en `/auth/me`: `is_premium` y `tutor_deep_access`;
- las respuestas de `/tutor/explain`, un texto de ejemplo por modo.

Lo que se mira aquí es la interfaz. El servidor está cubierto por
`backend/tests/integration/test_tutor_modes.py`.

- `pro-como-*`: Pro con «¿Cómo?» elegido.
- `pro-a-fondo-aviso-*`: Pro pulsa «A fondo». Sale para qué es Pro Max y no se llama al
  servidor; la prueba lo comprueba (`calls` = `why`, `how`).
- `promax-a-fondo-es-390`: Pro Max pide «A fondo» (`calls` = `why`, `deep`).

**axe (WCAG 2.2 AA):** 0 violaciones en cada captura.

La primera pasada encontró un fallo previo, ajeno a este cambio: el aviso tipo `info` («Bien
dicho…») tenía texto oscuro sobre `--le-blue-dark` en el tema oscuro, con un contraste de 3,75:1.
Ahora usa el fondo del aviso base.

**Nota sobre las capturas:** el servidor de desarrollo enseña los indicadores de depuración del
quiz, «Prob. acierto» y «Dominio %». Van detrás de `import.meta.env.DEV` y no salen en producción
(ADR-60).
