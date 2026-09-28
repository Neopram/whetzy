# Guión — Video Corto (60s) — Español

> **v2 (2026-09-26).** La narración y las escenas vigentes están en `scripts/video/escenas_es.json`, cada frase con su fuente; el vídeo se genera con `scripts/video/build_short.py` sobre capturas reales (`frontend/scripts/short-capture.cjs`). Sin música: no hay pista con licencia verificada.

## Objetivo
Viral TikTok/YouTube Shorts. Gancho rápido para career-switchers. Target: 18-35 años, redes sociales.

## Structure (Packed in 60 seconds)

### Hook (0:00-0:10)
- **Visual:** Rótulo grande: "¿Quieres aprender a programar sin perder el tiempo?"
- **Narración:** la misma frase
- **SFX:** Whoosh, beat drop

### Problem + Solution (0:10-0:45)
- **Visual:** Split screen montaje
  - **Left:** Competidor genérico (lento, aburrido)
  - **Right:** Whetzy (rápido, preguntas correctas)
- **Narración:** "Cada pregunta la elige un motor adaptativo, según lo que ya dominas."
- **Sin cifra de ahorro de tiempo:** el «47 % menos tiempo» y las «500 preguntas únicas» de la v1 no salían de ningún dato (línea roja: ninguna cifra sin fuente). Las cifras que sí valen son las de la landing (18 rutas · 6.305 preguntas, `catalog.ts`)
- **Visual:** Barrita de progreso llenándose rápidamente, emoji de fuego (racha)

### CTA (0:45-0:60)
- **Visual:** App screen, botón "Empezar" brilliant
- **Narración:** "Empieza gratis hoy. Sin tarjeta."
- **Overlay:** `whetzy.com` + `YT-ES-SHORT` (código de campaña bien visible)
- **SFX:** Positive chime, fade to black

## Technical Notes
- **Duration:** 58-62 seconds
- **Aspect ratio:** 9:16 (vertical for TikTok/Shorts)
- **Codec:** H.264, 4000 kbps
- **Audio:** Upbeat, trending sound (Incompetech or licensed track), fast cuts synced to beat
- **Campaign Code:** `YT-ES-SHORT`
- **Text:** Large, bold, high contrast (white on dark)
- **Subtitles:** Hard-coded ES (no autoplay audio requirement)
