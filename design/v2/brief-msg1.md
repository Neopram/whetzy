# Whetzy — UI/UX redesign prototype (frontend-only). Message 1 of 3.

> **Congelado** (nota del 2026-10-22, H.58): prompt histórico. El dueño sustituyó el acento por el cian
> `#00BFFF` el 2026-10-13; los colores vigentes están en `frontend/src/styles/design-tokens.css`.

You are designing the new interface of Whetzy, a bilingual (Spanish-first, English) web/mobile app where people learn programming and prepare IT certifications. This prototype will be PORTED by hand into an existing React 19 + Vite codebase that uses CSS Modules (not Tailwind), so the design system must be expressed as CSS variables. Credits are scarce: get it right in one pass, no placeholders, no lorem ipsum.

## 1. Brand decisions (final — do not reinterpret)
- Name: Whetzy (from "to whet" = afilar). Tagline ES: "Afila lo que sabes. Llega listo al examen." EN: "Sharpen what you know. Walk into the exam ready."
- Positioning: the instrument panel for your certification. Three things measured by an engine, not by a calendar: mastery per skill (Bayesian Knowledge Tracing), spaced review (FSRS), and readiness per official exam domain. Spanish-first, code runs in the browser.
- Personality: precise, calm, honest, premium-technical, adult. No mascot, no cartoon illustrations, no gamer-fantasy, no confetti spam.
- Honesty rules: no testimonials, no invented user counts, no countdown timers, no "70% OFF", no fake urgency.
- Differentiate from the attached competitor sheets (they show the quality bar, NOT something to copy): Brilliant = warm editorial serif; Duolingo & Mimo = cartoon mascots, bright; Codecademy = black/yellow terminal; Platzi = neon green on dark with instructor photos; Boot.dev = dark fantasy gold. Whetzy must look like none of them. Do not copy their layouts, copy or illustrations.
- The attached "whetzy-current-ui" sheet is what we are REPLACING. Its problems: 7 bottom tabs; unlabeled numbers in the top bar; every card the same weight and the same cyan; the core differentiator (readiness/mastery) is buried; rounded childish typography; lessons are a wall of text.

## 2. Visual system anchors (refine, but keep these)
- Dark theme is the default. Graphite: bg #0D1015, surface #151A21, surface-2 #1C222B, border #2A313C, text #E8ECF1, text-muted #93A0B0.
- Brand accent "chispa" (ember) #FF7A45 — used sparingly: primary buttons, the readiness fill, focus accents. Never as large background floods.
- Neutral data scale (mastery bars, charts): steel #5B7083 → ice #9CC9FF.
- Semantic: success #3DD68C, error #F2545B, attention/review-due #F5C04A.
- Light theme: warm paper bg #F6F5F2, ink #14171C, accent darkened enough to pass WCAG AA on paper.
- FORBIDDEN colors anywhere: #58CC02, #1CB0F6, #1899D6, #CE82FF.
- Tracks are NOT color-flooded: identify a track by its emoji/icon plus a small hue dot only.
- Typography: display headings = Bricolage Grotesque (variable, tight tracking); UI/body = Inter (variable); every number, percentage, timer, XP and all code = JetBrains Mono with tabular figures.
- Radius: 10–14px cards, 8px controls. Elevation via border + subtle inner light, not heavy drop shadows. Motion 150–250ms ease-out, and nothing moves when prefers-reduced-motion is set.

## 3. Hard technical constraints (the port depends on these)
1. ALL visual values live as CSS custom properties in `src/styles/tokens.css`, defined for `:root[data-theme="dark"]` (default) and `:root[data-theme="light"]`. If you use Tailwind, its config may ONLY reference these variables (e.g. `colors: { bg: 'var(--bg)' }`). No raw hex or arbitrary px values inside components (except 1px borders).
2. Frontend only. NO Supabase, NO auth backend, NO edge functions, NO database, NO API calls. All data comes from `src/fixtures/*.ts`, typed with the EXACT field names given in section 6 (they mirror our real API — do not rename fields).
3. Fonts self-hosted from npm only: `@fontsource-variable/bricolage-grotesque`, `@fontsource-variable/inter`, `@fontsource-variable/jetbrains-mono`. NEVER fonts.googleapis.com or any CDN. No external images or remote URLs at all. Icons: `lucide-react` only.
4. Real routes with react-router and a working browser Back button: `/hoy`, `/rutas`, `/rutas/:trackId`, `/practicar`, `/ranking`, `/yo`, `/leccion/:skillId`, `/quiz`, `/preparacion/:trackId`, `/design`. `/` redirects to `/hoy`.
5. i18n: Spanish default + English. Every UI string goes through a tiny `t()` dictionary in `src/i18n/es.ts` and `src/i18n/en.ts`. Content fields come in `*_es` / `*_en` pairs: pick by current language. Language toggle and theme toggle live in `/yo`.
6. Mobile-first at 390px wide, and excellent at 1280px: at ≥1024px a left sidebar replaces the bottom nav.
7. Accessibility: touch targets ≥44px, visible focus ring, WCAG AA contrast in both themes, semantic landmarks, aria-labels on icon buttons.
8. Small reusable components in `src/components/ui/` (one component per file, props typed). Pages in `src/pages/`. No dead code, no unused files, no demo leftovers from the template.

## 4. Information architecture
Bottom nav with exactly 5 tabs (labels always visible): Hoy (home), Rutas (tracks), Practicar (practice/review), Ranking (league + duels), Yo (profile, stats, wallet, settings).
Top bar: logo mark + wordmark on the left; on the right a single compact streak indicator with a label (e.g. "🔥 3 días"), never bare unlabeled numbers.

## 5. Scope of THIS message
A. `/design` — a living style guide: every token (color swatches for both themes, type scale, spacing, radii, elevation), plus these components showing ALL states (default/hover/focus/disabled/loading where relevant): Button (primary, secondary, ghost, danger), IconButton, Card (default, interactive, highlighted), Chip/Badge, Input, Tabs, ProgressBar, ReadinessGauge (0–100 arc with a marker at the 75% readiness threshold), DomainBar (a weighted bar per exam domain), StatTile, BottomNav, SideNav, TopBar, Toast, EmptyState, Skeleton.
B. App shell: TopBar + BottomNav/SideNav + routing. `/rutas`, `/practicar`, `/ranking`, `/yo` can be simple but real pages using the components (not "coming soon"); `/yo` must include the theme toggle and the ES/EN toggle.
C. `/hoy` — the home screen, fully designed:
   1. Hero "Tu preparación": a ReadinessGauge for the learner's goal certification, computed from the readiness fixture as readiness = Σ(weight_pct × p_known_mean) / Σ(weight_pct), shown as a percentage, plus "N de M dominios listos" (a domain is ready when `ready` is true) and the 75% threshold explained in one short line.
   2. One primary action "Siguiente paso": one concrete next step derived from the curriculum fixture (the first skill whose `lesson_seen` is false → "Lección · <skill name> · ~4 min"). Only ONE primary button on the screen.
   3. "Repaso pendiente" card driven by `reviews_due`; when 0 show a calm state ("Al día. Vuelve mañana.").
   4. Compact streak card: `current_streak`, `max_streak`, `streak_freeze_available` (called "comodín").
   5. "Tus rutas": `dashboard.tracks` as rows with mastery bars (`average_mastery`, `skills_mastered`/`total_skills`).
   Remove the generic "¿Listo para aprender?" hero and the empty 7-day grid.

Copy tone: direct, adult, neutral Latin-American Spanish using "tú".

## 6. Data contracts (synthetic sample values — keep the field names exactly)
```ts
// src/fixtures/me.ts
{ username: "ana_dev", display_name: "Ana", language: "es", is_admin: false }

// src/fixtures/dashboard.ts
{ level: 4, total_xp: 1240, current_streak: 3, max_streak: 9, streak_freeze_available: 1,
  last_active: "2026-10-01T17:33:01Z", reviews_due: 6, total_sessions: 18,
  total_questions_answered: 212, overall_accuracy: 0.71,
  tracks: [
    { track_id: "track01", name_es: "Python Básico", name_en: "Python Basics", icon: "🐍", color: "#4C8EDA", average_mastery: 0.42, skills_mastered: 14, total_skills: 52 },
    { track_id: "track09", name_es: "PCEP – Python Entry-Level Programmer", name_en: "PCEP – Python Entry-Level Programmer", icon: "🎓", color: "#D9A441", average_mastery: 0.28, skills_mastered: 4, total_skills: 15 } ] }

// src/fixtures/tracks.ts  (array)
{ id: "track01", name_es: "Python Básico", name_en: "Python Basics", order: 1, icon: "🐍", color: "#4C8EDA",
  total_questions: 867, is_certification: false, cert_provider: null, exam_question_count: null, exam_duration_minutes: null }
{ id: "track09", name_es: "PCEP – Python Entry-Level Programmer", name_en: "PCEP – Python Entry-Level Programmer", order: 9, icon: "🎓", color: "#D9A441",
  total_questions: 320, is_certification: true, cert_provider: "Python Institute", exam_question_count: 30, exam_duration_minutes: 40 }
// add 3–4 more plausible tracks (SQL, AWS Cloud Practitioner (cert), Ciberseguridad, Linux y Shell) with the same shape

// src/fixtures/curriculum.ts  (for track01)
{ track_id: "track01", name_es: "Python Básico", name_en: "Python Basics", icon: "🐍", color: "#4C8EDA", mastery_threshold: 0.95,
  modules: [ { id: "mod0101", name_es: "Fundamentos", name_en: "Fundamentals", order: 1,
      description_es: "Variables, tipos y operaciones básicas.", description_en: "Variables, types and basic operations.",
      min_mastery_to_unlock: 0, level: 1, average_mastery: 0.62, status: "in_progress", prerequisite_id: null, prerequisite_met: true,
      skills: [ { skill_id: "sk010101", name_es: "Variables y tipos", name_en: "Variables and types", order: 1, p_known: 0.81, mastered: false, attempts: 12, lesson_seen: true },
                { skill_id: "sk010102", name_es: "Operadores", name_en: "Operators", order: 2, p_known: 0.35, mastered: false, attempts: 4, lesson_seen: false } ] }
    // add 2 more modules: one in progress, one locked (prerequisite_met: false, min_mastery_to_unlock: 0.6), 3–4 skills each
  ] }

// src/fixtures/readiness.ts  (for track09)
{ track_id: "track09", domains: [
  { domain_id: "dom0901", name_es: "Fundamentos de Python", name_en: "Computer programming and Python fundamentals", weight_pct: 18, p_known_mean: 0.71, skills_assessed: 4, skills_total: 5, ready: false },
  { domain_id: "dom0902", name_es: "Flujo de control y funciones", name_en: "Control flow", weight_pct: 29, p_known_mean: 0.82, skills_assessed: 3, skills_total: 3, ready: true },
  { domain_id: "dom0903", name_es: "Estructuras de datos y módulos", name_en: "Data collections", weight_pct: 25, p_known_mean: 0.48, skills_assessed: 3, skills_total: 5, ready: false },
  { domain_id: "dom0904", name_es: "Funciones y excepciones", name_en: "Functions and exceptions", weight_pct: 28, p_known_mean: 0.30, skills_assessed: 1, skills_total: 2, ready: false } ] }

// src/fixtures/questions.ts  (used in message 3; create the file now)
{ id: "q-demo-1", skill_id: "sk010101", type: "mcq", difficulty_tier: "easy",
  question_es: "¿Cuál de estos es un nombre de variable válido en Python?", question_en: "Which of these is a valid Python variable name?",
  options_es: ["2var", "mi-var", "class", "_mi_var"], options_en: ["2var", "my-var", "class", "_my_var"],
  correct_answer_es: null, correct_answer_en: null, code_es: null, code_en: null, expected_time_ms: 15000 }
{ id: "q-demo-2", skill_id: "sk010101", type: "fill_blank_exec", difficulty_tier: "easy",
  question_es: "Completa el hueco para que el programa imprima `42`.\n\n```python\nx = ___\nprint(x)\n```",
  question_en: "Fill in the blank so the program prints `42`.\n\n```python\nx = ___\nprint(x)\n```",
  correct_answer_es: "42", explanation_es: "Cualquier expresión que evalúe a 42 sirve.", source: "CPython docs 3.13" }
```

## 7. Reply format
When done, reply with: the token file path and the list of tokens; the list of components with file paths; the list of routes; and any assumption you made. Keep the reply short.
