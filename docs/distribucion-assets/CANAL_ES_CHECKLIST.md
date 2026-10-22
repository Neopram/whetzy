# CANAL_ES_CHECKLIST — Ejecución Serie 26

**Responsable:** Usuario (canales)  
**Fecha inicio:** 2026-09-19  
**Deadline:** Semana 3 (cierre en domingo)

---

## SEMANA 1: RENDERIZADO

### Videos (26.0)

- [ ] **LUN** Scripts aprobados por owner
- [ ] **MAR** YT-ES-PROD renderizado (2 min, 1080p H.264, codec AAC)
  - Especificación: Producto overview, CTA clara, código YT-ES-PROD en super 1:30-1:45
- [ ] **MIE** YT-ES-MOTOR renderizado (5 min, 1080p H.264)
  - Especificación: Demo motor adaptativo, gamificación, código YT-ES-MOTOR en super
- [ ] **JUE** YT-ES-SHORT renderizado (60s, 1080p H.264)
  - Especificación: Hook "90% falla esto", código YT-ES-SHORT, directo al grano
- [ ] **VIE** Subtítulos: Auto-generated + manual QA (sin "Whetzy" mal traducido)
- [ ] **VIE** Thumbnails Canva (1280x720px, contraste alto, emoji + text ES)

### Verificación Técnica

- [ ] Audio: Sin ruido de fondo, nivelación uniforme (-18dBFS típico)
- [ ] Subtítulos: Legibles, timing correcto, gramática ES revisada
- [ ] Super codes: Posición 1:30-1:45, 3s hold, fallback a fade-to-black
- [ ] Metadata: Títulos, descripciones, tags ES correctos

---

## SEMANA 2: YOUTUBE + DEV.TO

### YouTube ES Uploads (26.0)

- [ ] **LUN** Upload YT-ES-PROD (programa para MAR 10:00 CET)
  - URL final: youtube.com/channel/[CHANNEL_ID]/videos?sort=dd
  - Descripción: Template en `docs/archive/26-PLANNING.md` (archivado, ADR-48)
  - Playlist: "Python para AI Engineers"
  - Notify: LinkedIn/Email cuando go-live
- [ ] **MAR** Upload YT-ES-MOTOR (YouTube Premiere, MAR 21:00 CET)
  - Wait-for-live: 10 min antes de Premiere, revisar thumbnail
- [ ] **MIE** Upload YT-ES-SHORT (Shorts feed)
  - Verificar: Aparece en feed, super legible en móvil

### YouTube Engagement (During Week 2-3)

- [ ] Monitor primeras 24h: Views, likes, comments
- [ ] Respond to top 5 comments (ES, profesional)
- [ ] Pin top comment con CTA: "Código: YT-ES-PROD en descripción"

### Dev.to Articles (26.1)

- [ ] **JUE** Publish Article #1: "Motor adaptativo de Whetzy: arquitectura interna"
  - Wordcount: 1,500+
  - Tags: #python #learning #ai #spanish #adaptive-learning
  - CTA final: "Prueba en whetzy.com (ref=DEV-ES-1)"
  - Cover: Screenshot motor o diagrama arquitectura
  - Draft: 24h antes en plataforma, QA de typos

- [ ] **VIE** Publish Article #2: "Gamificación con Python: 7 patrones para retener usuarios"
  - Wordcount: 1,200+
  - Tags: #python #gamification #edtech #learning
  - Code snippets: 2-3 ejemplos reales (XP, badges, streaks)
  - CTA: "Aplicado en Whetzy (ref=DEV-ES-2)"

### Dev.to Metrics

- [ ] Verify articles live in Dev.to/search
- [ ] Share in relevant DEV communities (Discord, Slack)

---

## SEMANA 3: LINKEDIN + MEDICIÓN

### LinkedIn Posts (sin fila en el ledger: 26.3 es el email a universidades)

**Horario:** 9:00 CET (máximo alcance LATAM)

- [ ] **LUN** Post #1: "¿Por qué fallan 90% de plataformas EdTech en LATAM?"
  - Tone: Problema → datos → solución
  - CTA: "whetzy.com (ref=LI-ES-1)"
  - Length: 200-300 caracteres
  - Image: Stat graphic o screenshot (1200x628px)

- [ ] **MAR** Post #2: "Whetzy: AI + pedagogía. Las cifras." (sin cifra de retención hasta tener evidencia; H.58)
  - Tone: Data-driven, humilde
  - CTA: Link whetzy.com (rotate ref=LI-ES-1)
  - Engage: Invite debate en comments
  - Image: Chart retention rates

- [ ] **MIE** Post #3: "Python para AI Engineers — en español, hoy mismo"
  - Tone: Feature announcement
  - CTA: "Gratuito, sin tarjeta. whetzy.com"
  - Image: Logo + testimonial (si existe)

- [ ] **JUE** Post #4: "Las 3 habilidades que Platzi/DataCamp NO enseñan"
  - Tone: Thought leadership, controversia positiva
  - CTA: "Aprende las 3 en Whetzy"
  - Image: Diagram skills gap

- [ ] **VIE** Post #5: "Certificado verificable vs. curso genérico: ROI real"
  - Tone: Professionalismo, numbers
  - CTA: "Tu certificado en Whetzy"
  - Length: 150-250 caracteres

### LinkedIn Engagement

- [ ] Respond to comments within 4h (professional tone)
- [ ] Like relevant replies
- [ ] Share own posts to story (amplify reach)

### Measurement & Reporting (EOW Semana 3)

**Analytics Dashboard Capture:**

- [ ] YouTube Stats:
  - [ ] Views per video (YT-ES-PROD / MOTOR / SHORT)
  - [ ] Average watch duration
  - [ ] CTR via link-in-description
  - [ ] Subscriber growth (baseline → end week 3)

- [ ] Dev.to Stats:
  - [ ] Article views (total + per piece)
  - [ ] Reactions + comments per article
  - [ ] Link-outs tracked (if DEV tracking active)

- [ ] LinkedIn Stats:
  - [ ] Impressions (sum 5 posts)
  - [ ] Engagement rate (reactions + comments)
  - [ ] Clicks to external (whetzy.com)
  - [ ] Profile views spike

- [ ] **CRITICAL:** Cohort signups:
  - [ ] Total new users via ref=YT-ES-* 
  - [ ] Total new users via ref=DEV-ES-* 
  - [ ] Total new users via ref=LI-ES-1
  - [ ] D1 retention % (users active day 2)
  - [ ] D7 retention % (users active day 8)

**Output:** Compile COHORT_REPORT_26.0_RESULTS.md with numbers + narrative

---

## ONGOING (Semana 4+)

- [ ] Monitor YouTube comments daily (respond <12h)
- [ ] Track cohort analytics weekly (retention curves)
- [ ] Adjust messaging if D7 retention < 10%
- [ ] Prepare Series 27 (EN equivalent) based on learnings

---

## SIGN-OFF

**Planned by:** Claude Haiku 4.5  
**Reviewed by:** [User]  
**Date started:** [Date]  
**Date completed:** [Date]

- [ ] All items checked before submit
- [ ] Metrics compiled + reviewed
- [ ] Next series (27.0 EN) planning starts
