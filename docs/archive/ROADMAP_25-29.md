# Roadmap Ejecutable — Series 25-29 Completas

**Generado:** 2026-09-19 (sesión bj)  
**Estado:** Todos los gates desbloqueados (H.22, H.23, H.24, H.26, H.29, H.20, H.10)  
**Objetivo:** Completar las 5 series para launch total

---

## Arquitectura de Dependencias

```
H.29 Decisión Fiscal (USER INPUT PENDIENTE)
  ├─ Serie 21: Entidad + Rail (21.1, 21.2) → 21.7 legal review
  ├─ Serie 28: Payouts instructores (depend 21.1, 21.2)
  └─ Serie 29: Economía cerrada (depend 21.1)

H.22 OWASP ✅ (Confirmado)
  └─ Serie 25: Tracks seguridad 13, 24, 25

H.23 Canales ES ✅ (Confirmado)
  └─ Serie 26: Videos + distribución masiva ES

H.24 Admin ✅ (Confirmado, espera 22.1 DONE)
  └─ Serie 28: Marketplace instructores

H.26 Economía ✅ (Confirmado)
  └─ Serie 29: Créditos, referidos, wallet

Crítico: 20.7 CI (verificación). Hoy falló, requiere revisión.
```

---

## Serie 25: Expansión Contenido (Tracks Seguridad)

**Estado:** TODO | Depende H.22 ✅  
**Tamaño:** 15 tareas (ver AUTONOMOUS_STATE.md §25)  
**Prioridad:** PRI 0-2

### Tareas Principales
| ID | Descripción | Estimado |
|---|---|---|
| **25.0** | Planificación roadmap | 1-2h |
| **25.5** | 3 tracks seguridad (NIST+OWASP) | 40-60h |
| **25.14** | ~50 animaciones Manim | 80-120h |
| 25.1-25.4, 25.6-25.13 | Otros tracks (ML, Data, Cloud, etc.) | 200+ h |

### 25.5 Desglose (Crítica)
- **track13:** Ciberseguridad Fundamentos (1.200 Q, NIST+OWASP)
- **track24:** Penetration Testing (1.200 Q, WSTG+ATT&CK)
- **track25:** Cloud Security (1.200 Q, NIST CSF+ASVS)
- Cada track: 12 skills, 3-4 módulos, ≥15% ejecutable

### Milestones
- **25.0:** Hoy (documento)
- **25.5:** 7-10 días (3 tracks × ~2-3 días cada uno)
- **25.14:** Post-25.5 (Manim depende que otros tracks estén listos para videos)

---

## Serie 26: Distribución Masiva ES

**Estado:** TODO | Depende H.23 ✅ (canales creados por usuario)  
**Tamaño:** 9 tareas  
**Prioridad:** PRI 0-2

### Tareas Principales
| ID | Descripción | Dependencia |
|---|---|---|
| **26.0** | Estrategia de lanzamiento ES | H.23 ✅ |
| **26.1-26.3** | 3 videos demo (producto, motor, short) × ES | 24.13 (guiones) ✅ |
| **26.4-26.6** | Distribución: YouTube, Dev.to, DevRelación | 26.1-26.3 |
| **26.7** | Medición: analytics, código campaign | 26.4-26.6 |
| **26.8** | Superteam LATAM partnership | Independiente (H.28) |

### Canales Requeridos (Usuario Debe Crear)
- YouTube channel: Whetzy ES
- Dev.to profile: whetzy-es o similar
- LinkedIn page: Whetzy (if not already)

### Timeline
- **Hoy:** 26.0 (estrategia)
- **Semana 1:** 26.1-26.3 renderizado de videos
- **Semana 2:** 26.4-26.6 lanzamiento + distribución
- **Semana 3+:** 26.7 medición + 26.8 Superteam

---

## Serie 28: Marketplace Instructores

**Estado:** TODO | Depende 22.1, 22.3, H.24 ✅  
**Tamaño:** 8 tareas  
**Prioridad:** PRI 1-2

### Tareas Principales
| ID | Descripción | Estimado |
|---|---|---|
| **28.0** | Planificación marketplace | 2-3h |
| **28.1-28.3** | UI instructor panel + course upload | 10-15h |
| **28.4** | Revenue split y comisiones (por rail en 21.2) | 5-8h |
| **28.5** | Estudiante → instructor checkout flow | 5-8h |
| **28.6** | Facturación instructor | 8-12h |
| **28.7** | Payouts autom. (depende 21.1) | 10-15h |

### Bloqueos Críticos
- **21.1 Entidad:** ¿Italia o Grecia? (user input en H.29)
- **21.2 Rail:** ¿Stripe, Paddle, IAP? (user input en H.29)
- **22.1 Admin:** Panel must be DONE (hoy está PARCIAL)

### Timeline
- **Hoy:** 28.0 (hoy) + esperar H.29 decisión
- **Semana 1:** 28.1-28.3 UI (paralelo a H.29 análisis backend)
- **Semana 2:** 28.4-28.6 financial logic (depende 21.2 decisión)
- **Semana 3:** 28.7 payouts (depende 21.1+21.2)

---

## Serie 29: Economía Cerrada

**Estado:** TODO | Depende 24.6, H.26 ✅, H.29 ⏳  
**Tamaño:** 13 tareas  
**Prioridad:** PRI 1-2

### Tareas Principales (de ECONOMIA.md §1-3)
| ID | Descripción | Estimado |
|---|---|---|
| **29.0** | Reglas de créditos y grifos/sumideros | 3-5h |
| **29.1** | Ledger de transacciones (backend) | 8-12h |
| **29.2** | Wallet UI (frontend) | 5-8h |
| **29.3** | Canje de créditos por características | 5-8h |
| **29.4** | Códigos de campaña (campañas masivas) | 3-5h |
| **29.6** | Atribución por referido (con 28) | 8-12h |
| **29.8** | Gamificación integrada (con 24.6) | 5-8h |
| **29.10** | cNFTs Open Badges (opcional H.27) | 5-10h |
| **29.11** | Cláusulas legales en ToS/Privacy | 3-5h |

### Reglas de Economía (de ECONOMIA.md §2-3)
**Grifos (Ingresos):**
- Pagos de suscripción
- Sponsors de tracks
- Grants Solana (H.28)

**Sumideros (Gastos):**
- Créditos gratis (onboarding: 5 créditos)
- Referidos (K-factor multiplier)
- Instructor payouts

**Tasa de canje:** 1 crédito = €0.10 (o según ECONOMIA.md §3)

### Timeline
- **Hoy:** 29.0 (reglas)
- **Semana 1:** 29.1-29.2 (backend + wallet)
- **Semana 2:** 29.3-29.6 (canje + atribución)
- **Semana 3:** 29.8 (gamificación integrada) + 29.10 (NFT opcional)

---

## Serie 21: Legal y Fiscal (Dependiente de H.29)

**Estado:** PARCIAL (21.0 DONE; 21.1, 21.2, 21.7 TODO)  
**Critica:** Bloquea 28 y 29

### 21.1 Entidad Fiscal (H.29 Input)
- Italia: forfettario 5%, Stripe personal
- Grecia: renta 22%, Paddle MoR
- Crear backend/app/models/payment.py (parametrizado)

### 21.2 Rail de Pagos (H.29 Input)
- Stripe personal (si Italia)
- Paddle (si Grecia o multinacional)
- IAP + Paddle (híbrido web+mobile)

### 21.7 Textos Legales (H.20 Review)
- ToS, Privacy Policy, etc. revisados por abogado
- Hoy: BORRADOR visible
- Post-H.20: FINAL (o diferido hasta MRR)

---

## Serie 20: Verificación (Crítica)

**Estado:** 9/11 DONE | 20.7 ❌ FALLÓ, 20.10 TODO

### 20.7 CI Verification (PRI 1)
- verify_ci_local.ps1 falló con exit 1 (9 failures)
- Backend: pip-audit, ruff, mypy, pytest
- Frontend: tsc, oxlint, vitest, build, i18n
- **Acción:** Debug CI, fix errores de lint/type

### 20.10 Regresión de Dieta (PRI 2)
- AUTONOMOUS_STATE.md debe estar < 60 KB
- Hoy: ~107 KB (regresión de +56 KB)
- **Acción:** Guardia mecánica en check_docs.py

---

## Plan de Ejecución Propuesto

### Hoy (Sesión bj)
- [x] Fase 1: H.29 Análisis Fiscal ✅
- [ ] Fase 2: 20.7 CI Debug (depende diagnosis)
- [ ] Fase 3: 22.1 Admin Completar (paralelo)
- [ ] Fase 4: Serie 25 Scaffolding (Agent en bg)
- [ ] Fase 5: Serie 26 Planning (documento)

### Semana 1
- Serie 25.5 (3 tracks seguridad)
- Serie 26 renderizado de videos
- Serie 28 UI + financiero
- Serie 29 reglas de créditos
- Serie 21 backend payment model (depende H.29 decisión)

### Semana 2+
- Series 25 contenido completo
- Series 26-29 integración + testing
- Legal reviews (H.20)
- Deploy (H.SEED)

---

## Checklist de Bloqueos Pendientes

- [ ] **H.29:** Usuario cuenta días en Grecia 2026 → Escenario A o B
- [ ] **H.20:** Abogado revisa textos legales
- [ ] **H.10:** 30 usuarios beta simulados (creado scaffolding hoy)
- [ ] **H.23:** YouTube/Dev.to canales creados (usuario)
- [ ] **20.7:** CI debug y fix de errores

---

## Métricas de Progreso

| Serie | Antes | Ahora | Goal |
|---|---|---|---|
| 25 | 0/15 BLOCKED | 0/15 TODO | 15/15 ✅ |
| 26 | 0/9 BLOCKED | 0/9 TODO | 9/9 ✅ |
| 28 | 0/8 BLOCKED | 0/8 TODO | 8/8 ✅ |
| 29 | 0/13 BLOCKED | 0/13 TODO | 13/13 ✅ |
| 21 | 1/6 PARCIAL | 1/6 TODO* | 6/6 ✅ |
| 20 | 9/11 DONE | 9/11 DOING | 11/11 ✅ |

*Wait for H.29 user input

---

Documento actualizado continuamente. Próxima revisión: mañana (o cuando H.29 tenga input del usuario).
