# Message 2 of 3 — the learning loop. Same rules as message 1 (tokens only, fixtures only, no backend, no CDN, ES/EN, a11y, no dead code). Reuse the existing components in src/components/ui; add new ones there only if needed.

Design these screens fully, with real interactions on fixture data:

## A. `/rutas` — track catalogue
- Two filter chips: "Aprender" (is_certification=false) and "Certificaciones" (is_certification=true), plus "Todas".
- Each track is a row/card: icon + small hue dot, name, total_questions, and for certifications a meta line "30 preguntas · 40 min · Python Institute" from exam_question_count / exam_duration_minutes / cert_provider. Learner's mastery bar if the track is in dashboard.tracks.

## B. `/rutas/:trackId` — track detail (use curriculum fixture for track01; for others show the same structure with fixture data)
- Header: icon, name, overall mastery (mean of module average_mastery) as a precise mono percentage.
- A compact "Prueba de nivel" banner: "¿Ya sabes algo? Haz la prueba de nivel y sáltate lo que dominas." (secondary button).
- If the track is a certification: two cards "Simulacro de examen" (exam_question_count + exam_duration_minutes) and "Preparación por dominio" (links to /preparacion/:trackId). If not a certification: one card "Examen final del curso" (50 preguntas · 75 min · se aprueba con 70%).
- Modules as a vertical progression: each module shows name, level, status (in_progress / completed / locked), average_mastery bar. Locked modules show the reason: "Se desbloquea con 60% en <prerequisite name>" using min_mastery_to_unlock and prerequisite_id.
- Expanding a module lists its skills: p_known as a mono % and a 5-segment mastery meter; mastered skills get a check. Two actions per module: "Lección" (ghost) and "Practicar" (primary) — "Practicar" is disabled with a tooltip "Primero ve la lección" when no skill in the module has lesson_seen=true.

## C. `/leccion/:skillId` — lesson (replace the wall of text)
- Stepped lesson: 3–5 short cards (concept → example → common mistake → mini-check), progress dots at top, ← / → controls, keyboard arrows work.
- The example card shows a code block (JetBrains Mono, syntax-colored using only tokens) with a "▶ Ejecutar" button that reveals a pre-baked output panel (no real execution needed in the prototype).
- Source line at the bottom ("Fuente: CPython docs 3.13") — every lesson cites its source.
- Final step CTA: "Practicar esta habilidad" → /quiz?skill=<skillId>.
- Write the lesson content for sk010101 "Variables y tipos" in ES and EN (short, accurate Python).

## D. `/quiz` — practice session (use questions fixture; loop both questions)
- Top: thin progress bar, question counter "2 / 10" in mono, close (X) with confirm "¿Salir? Tu progreso se guarda.", difficulty chip, and a small "por qué esta pregunta" chip that shows on tap: "Elegida porque tu dominio de <skill> es 35%".
- mcq: options as large rows with A/B/C/D keys (keyboard 1–4 and A–D work). States: idle, selected, correct (success token + check), wrong (error token + x, correct one revealed), dimmed others.
- fill_blank_exec: code block with an inline input in the blank, "▶ Ejecutar" button, output panel showing expected vs got, then correct/wrong state.
- "No lo sé" ghost button always available before answering (it is a real signal for the engine, never shamed).
- After answering: explanation card with source line, a "¿Por qué?" button (opens a side sheet "Tutor" with a short pre-written explanation — no AI call), and "Siguiente" primary button.
- End screen after 10: accuracy, XP gained (mono), skills that moved (before → after p_known as mini bars), next recommended action. No confetti; a single subtle success animation.

## E. `/preparacion/:trackId` — readiness by domain (use readiness fixture)
- Hero ReadinessGauge with the weighted readiness (same formula as /hoy) and threshold 75%.
- One DomainBar per domain, ordered by weight_pct, showing weight_pct ("18% del examen"), p_known_mean as %, skills_assessed/skills_total, and a ready badge.
- The weakest heavy domain gets a highlighted card "Tu mayor palanca: <domain> — vale 28% del examen y estás en 30%." with a primary "Practicar este dominio".
- Secondary action: "Hacer simulacro".
- A one-line honest explanation: "El porcentaje es la probabilidad estimada de que domines cada habilidad (BKT), ponderada por el peso oficial de cada dominio."

## F. Exam shells (static but complete): from the track detail, the "Simulacro" and "Examen final" cards open an intro sheet with the rules (question count, minutes, pass mark, "las preguntas sin responder cuentan como falladas") and a "Empezar" button that goes to an exam view: question navigator grid (answered / flagged / pending), mono countdown timer (static is fine), Anterior / Siguiente, "Marcar para revisar", and "Entregar" with a confirmation listing unanswered count.

Reply with the new routes, new components and file paths only.
