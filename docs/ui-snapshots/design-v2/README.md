# Capturas — design/v2, pasos 4 a 7 (Rutas, Lección, Quiz, Preparación y Exámenes)

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
- `07-preparacion-390.png`: preparación de AWS CLF-C02 para un usuario sin
  práctica: arco con la marca del 75 %, la nota de que el % es el punto de
  partida del modelo, la mayor palanca y los dominios ordenados por peso.
- `07b-simulacro-intro-390.png`: intro con formato y reglas.
- `07c-simulacro-en-curso-390.png`: examen con reloj en mono, una pregunta
  marcada y la cuadrícula abierta.
- `07d-simulacro-confirmar-390.png`: confirmación al entregar con preguntas en
  blanco.
- `07e-simulacro-resultado-390.png`: resultado por dominio.
- `08-yo-390.png`: Yo tras una pregunta respondida y la sesión abandonada: el
  XP (15) ya coincide con Estadísticas y la barra superior; Pro sin dorado.
- `08b-estadisticas-390.png`: cifras en mono, solo las rutas empezadas (con el
  recuento de las que no) y dominio por habilidad en azul.
- `08c-cartera-390.png`: solo lo que el backend cablea hoy: el comodín de racha
  y el código promocional; sin «Cómo ganar créditos» ni «Invitar amigos»,
  porque nada abona créditos por estudiar ni por referido.
- `08d-duelo-reto-390.png`: reto con rival y habilidad (por defecto, una de las
  practicadas).
- `08e-landing-1280.png`, `08f-landing-claro-390.png`: landing en grafito, con
  el acento solo en la acción principal; el tema claro ya no hereda blancos
  fijos.
- `08g-landing-preparacion-1280.png`: la sección de preparación con la captura
  nueva.
- `09-cartera-referido-390.png`: Cartera de un usuario que se registró con el
  enlace `/r/<código>` de otro e hizo el onboarding real: 200 créditos de
  bienvenida que caducan a los 30 días, las condiciones de activación, los hitos
  de la escalera y su propio código para invitar (ADR-57).

axe-core (WCAG 2.2 AA) dio 0 violaciones en Yo y Estadísticas y en la landing
(tests nuevos de `e2e/accessibility.spec.ts`), y en Rutas y en el feedback del Quiz
(`e2e/accessibility.spec.ts`), y en la lección, la pregunta, la confirmación
de salida y el resumen del Quiz, y en Preparación y las cuatro fases del
simulacro (comprobaciones ad hoc de la sesión).
