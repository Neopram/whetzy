# Whetzy — Decisiones de Identidad Visual · 24.0/24.1
**Navegación competitiva verificada en vivo: 2026-09-19**

---

## 1. Competidoras Analizadas

| Plataforma | Color Primario | Lección para Whetzy |
|-----------|---|---|
| **Duolingo** | Bright Green | NO casual; somos technical |
| **DataCamp** | Dark + Cyan | Dark mode = credibility; EN ESPAÑOL diferencia |
| **Brilliant** | Minimalist | Elegancia sin clutter; BKT territory map anchor |
| **Codecademy** | Black + Yellow | Accesible pero evitar neon; somos serio |
| **Educative** | Navy #001E3C | MÁS PARECIDO; copiar credibility language |
| **Udemy** | Orange/Purple | Evitar lifestyle; somos técnico |
| **freeCodeCamp** | Dark gradient | Monospace = developer credibility |
| **Coursera** | Blue #0066E5 | Ratings + social proof; Open Badges ancla |

---

## 2. Decisiones Whetzy

### Color Primario: Sky Blue #1CB0F6 (sustituido el 2026-10-13 por el cian del logo `#00BFFF`; valores vigentes en `frontend/src/styles/design-tokens.css` y `design/brand/README.md`)
- Accessible WCAG AA, modern, technical
- Dark mode DEFAULT (como Educative, DataCamp, freeCodeCamp)

### Full Color System (sustituido el 2026-10-13: ver `design-tokens.css`; fondo oscuro hoy `#0A0E1A`, claro `#F5F7FB`):
- Primary: #1CB0F6 (hover #1A90D2)
- Success: #10B981 (SOLO para éxito)
- Dark bg: #0F172A | Light bg: #F9FAFB
- Text light: #1F2937 | Text dark: #E5E7EB
- Accent: #6366F1 | Warning: #F59E0B | Error: #DC2626

### Tipografía (sustituida: hoy Inter / Bricolage Grotesque / JetBrains Mono, `--le-font*`):
- Headlines/Body: System sans (-apple-system, Roboto)
- Code: Monospace (Monaco, Fira Code)
- NO serif (developer-first, not math-first)

### Espaciado (8px base):
- --space-4: 2rem [DEFAULT PADDING]
- --radius-md: 8px [DEFAULT]
- --transition-normal: 300ms cubic-bezier(0.4, 0, 0.2, 1)

---

## 3. Visual Anchors Únicos

### BKT Territory Map
Skill landscape explorable: cian `#06B6D4` (frontera; paleta Obsidian de la serie 34, ADR-47 — antes «azul cielo») + verde (dominado 15%+) + naranja (parcial)

### FSRS Repaso Timeline
Calendario con próximos repasos como eventos; fechas próximas en cian `#06B6D4` (paleta Obsidian, ADR-47)

### Elo Level Badges
Nivel como rank visual (icono + número + barra hacia siguiente nivel)

---

## 4. Qué NO Haremos
- ❌ Mascota tipo Duolingo — *enmendado el 2026-10-19 (ADR-67 D2): habrá mascota, en SVG + Lottie, tranquila y
  técnica como pide `design/v2/GUIA.md`; lo que sigue fuera es una caricatura ruidosa al estilo Duolingo.*
- ❌ Neon colors tipo Codecademy
- ❌ Lifestyle photos tipo Udemy
- ❌ Corporate navy tipo Coursera
- ❌ Serif headlines tipo Brilliant
- ❌ RPG gamification

---

**Espíritu:** Elegancia técnica (Brilliant) + credibilidad developer (Educative) + acceso gratuito (freeCodeCamp) + territorio adaptativo único — TODO EN ESPAÑOL/INGLÉS NATIVO.
