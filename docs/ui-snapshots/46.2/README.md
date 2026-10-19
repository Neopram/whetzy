# Capturas — 46.2, interruptores de sonido y vibración en Perfil

Evidencia del PR de la fila 46.2 (`docs/PLAN_UI_AVANZADA.md` §6). Capturas del
2026-10-18, tomadas con Playwright (Chromium) contra el stack local (Postgres 16
+ Redis, backend en `:8000`, Vite en `:5199`), con una cuenta registrada de cero
en cada captura: no hay datos inventados. axe (WCAG 2 A/AA) dio 0 violaciones en
las cuatro combinaciones de idioma y ancho, con el sonido ya encendido.

- `perfil-{es,en}-{390,1280}-apagado.png`: Ajustes de una cuenta nueva.
  «Sonidos» / «Sounds» arranca **apagado** (por defecto, plan §6.0) y
  «Vibración» / «Vibration» encendido.
- `perfil-{es,en}-{390,1280}-sonido-encendido.png`: la misma pantalla tras
  pulsar «Sonidos»: el interruptor pasa a encendido (`aria-checked="true"`).

En inglés, el idioma se cambió con el selector ES/EN de la propia pantalla.
