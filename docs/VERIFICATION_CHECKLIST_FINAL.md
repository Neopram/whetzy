# Verificación Final — 7 Puntos de Decisión Humana

> Checklist para confirmar al cierre de sesión (100% de tareas terminadas) que cada decisión se implementó correctamente.

**Decisión registrada:** 2026-09-19 (sesión bj)

---

## ✅ H.29: Entidad Fiscal y Rails de Pagos

**Decisión del usuario:**
- **Residencia:** Grecia (turista, contabilizar días ≥183 en 2026)
- **Rails de pagos:** Investigar los tres (Stripe personal + Paddle/Lemon Squeezy + solo IAP)
- **Entidad:** Depende de días en Grecia (Italia si <183, Grecia si ≥183)

**Verificar al cierre:**
- [ ] Documento `docs/legal/H29-DECISION-LOG.md` creado con comparativa
- [ ] Filas 21.1, 21.2, 21.7 pasadas a TODO
- [ ] backend/app/models/payment.py creado (schema neutral)
- [ ] Commit: "H.29: Decisión fiscal — Italia/Grecia + 3 rails de cobro"

---

## ✅ H.22: OWASP en Seguridad

**Decisión:** SÍ — CC BY-SA 4.0 aceptada

**Verificar:**
- [ ] tracks 13, 24, 25 (Ciberseg, Pentest, Cloud Sec) con OWASP + NIST + MITRE
- [ ] Cabecera CC BY-SA en docs
- [ ] DECISIONS.md ADR-11 actualizado
- [ ] Commit: "H.22: Aceptar CC BY-SA — tracks seguridad"

---

## ✅ H.23: Serie 26 ES

**Decisión:** Confirmado

- [ ] Serie 26: BLOCKED → TODO
- [ ] Canales YouTube/Dev.to creados (usuario)
- [ ] Checklist `docs/distribucion-assets/CANAL_ES_CHECKLIST.md`
- [ ] Commit: "H.23: Abrir Serie 26 — canales ES"

---

## ✅ H.24: Serie 28 Marketplace

**Decisión:** Confirmado

- [ ] Serie 28: BLOCKED → TODO
- [ ] instructor.py + migraciones Alembic
- [ ] Commit: "H.24: Abrir Serie 28 — marketplace"

---

## ✅ H.26: Serie 29 Economía

**Decisión:** Confirmado

- [ ] Serie 29: BLOCKED → TODO
- [ ] ECONOMIA.md §1–3 confirmado
- [ ] economy.py + credit_transactions
- [ ] Commit: "H.26: Abrir Serie 29 — economía"

---

## ✅ H.20: Abogado Legal

**Decisión:** Sí, disponible

- [ ] H29-REVISION_PLAN.md con scopeo
- [ ] 21.7 sigue HUMAN-BLOCKED hasta revisión completa
- [ ] Commit: "H.20: Abogado identificado"

---

## ✅ H.10: Beta Simulada

**Decisión:** 30 usuarios simulados

- [ ] beta_users.py (30 usuarios: beginner/intermediate/advanced)
- [ ] seed_beta_cohort.py script
- [ ] test_beta_cohort_metrics.py valida D1≥40%, D7≥20%, Δp_known≥+0.20
- [ ] Commit: "H.10: Cohorte beta simulada (30 usuarios)"

---

## 📊 Series Desbloqueadas

| Serie | Antes | Ahora | Gate |
|---|---|---|---|
| 25 | BLOCKED | TODO | H.22 ✅ |
| 26 | BLOCKED | TODO | H.23 ✅ |
| 28 | BLOCKED | TODO | H.24 ✅ |
| 29 | BLOCKED | TODO | H.26 ✅ |
| 21 | HUMAN-BLK | TODO | H.29 ✅ |

**Roadmap:** H.29 → 20.7 → 22.1/22.3 → 25 → 26 → 28 → 29 = Launch.
