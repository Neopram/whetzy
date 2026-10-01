# Capturas — design/v2, pasos 4 a 6 (Rutas, Lección y Quiz)

Evidencia del PR de los pasos 4 y 5 del port (`design/v2/GUIA.md`). Capturas
frescas del 2026-10-01, tomadas con Playwright (Chromium) contra el stack local
(Postgres 16 + Redis, sin Docker), con usuarios registrados de cero en la
misma sesión: no hay datos inventados.

- `04-rutas-detalle-390.png`: detalle de Python Básico a 390 px tras un quiz de
  10 preguntas (cabecera con dominio medio de módulos, prueba de nivel, examen
  final, currículo por niveles).
- `04b-rutas-modulo-390.png`: el primer módulo desplegado: habilidades con
  medidor de 5 tramos y % exacto, «Aprender» y «Practicar»; los módulos
  bloqueados dicen con qué % y en qué módulo se desbloquean.
- `04c-rutas-catalogo-390.png` y `04d-rutas-certificaciones-390.png`: el
  catálogo, sin filtro y filtrado por certificaciones (formato del examen y
  proveedor en cada fila).
- `04e-rutas-aws-1280.png`: detalle de una certificación (AWS CLF-C02) a
  1280 px: simulacro + preparación por dominio, sin examen final.
- `05-leccion-concepto-390.png`: primer paso de la lección de Variables.
- `05b-leccion-salida-390.png`: último paso, el ejemplo con la salida ya
  pedida y el botón de practicar.
- `05c-leccion-1280.png`: un paso de texto a 1280 px.
- `06-quiz-pregunta-390.png`: pregunta con contador en mono, dificultad, motivo
  de la elección y opciones con su tecla.
- `06b-quiz-feedback-390.png`: explicación con fuente, «¿Por qué?» como botón
  secundario y «Siguiente».
- `06c-quiz-salir-390.png`: confirmación al cerrar con algo ya respondido.
- `06d-quiz-resumen-390.png`: resumen con precisión, aciertos, racha y XP en
  mono, la habilidad de la sesión («nueva → 24 %») y la acción recomendada.

axe-core (WCAG 2.2 AA) dio 0 violaciones en Rutas y en el feedback del Quiz
(`e2e/accessibility.spec.ts`), y en la lección, la pregunta, la confirmación
de salida y el resumen del Quiz (comprobaciones ad hoc de la sesión).
