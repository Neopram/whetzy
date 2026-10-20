# Capturas: duelo con la partida grabada del rival

Evidencia del PR del duelo con la partida grabada: quien juega segundo ve, tras contestar
cada pregunta, si el rival la acertó y en cuánto tiempo. Captura del 2026-10-20 con
Playwright (Chromium) contra el stack local (Postgres 16 + Redis, backend en `:8000`,
Vite en `:5199`), con dos cuentas registradas de cero. La genera
`frontend/e2e/duelo-grabado.spec.ts`.

- `rival-por-pregunta-es-390.png`: el segundo jugador acaba de contestar la pregunta 1.
  Debajo de las opciones, «✗ <rival> falló esta (1,3 s)». Son los datos que el servidor
  guardó de la partida del retador (`challenger_answers`), no inventados: el spec hace
  esperar al retador ~1,3 s antes de cada respuesta para que el tiempo sea de persona.

El primer jugador no ve nada del rival (aún no ha jugado), y el segundo no lo ve antes
de contestar. axe (WCAG 2.2 AA) con el resultado del rival a la vista: 0 violaciones.
