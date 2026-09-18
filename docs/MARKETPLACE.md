# Whetzy — Marketplace de Profesores e Instructores

> **Documento vivo nº 15.** Spec completo del marketplace: roles, revenue share,
> quality gate, moderación y flujo técnico. Serie 28 implementa esto.
> Última actualización: 2026-09-18 (sesión bh).

---

## 0. Por qué un marketplace

Whetzy construye contenido con Haiku + fuentes [reusar]. Eso cubre los 27 tracks
del catálogo oficial. Pero hay conocimiento especializado que un instructor humano
puede aportar mejor que un modelo: casos reales de empresa, nichos muy específicos,
cursos de herramientas nuevas del mercado.

El marketplace resuelve dos problemas a la vez:
1. **Velocidad de contenido:** 20 instructores activos = 20x la velocidad de producción
2. **Credibilidad:** Contenido de practitioners reales con trayectoria verificable

Boot.dev no tiene marketplace. DataCamp no tiene. Platzi tampoco.
Udemy tiene marketplace pero sin motor adaptativo y con revenue share de 25-37%.
**Whetzy ofrece 70% + el mejor motor del mercado.**

---

## 1. Roles en el sistema

| Rol | Qué puede hacer | Cómo se activa |
|---|---|---|
| `student` | Aprender, comprar cursos, ver certificados | Registro estándar |
| `instructor` | Crear y vender cursos en el marketplace | Solicitud + aprobación manual |
| `company_admin` | Gestionar empresa, asignar cursos, ver métricas del equipo | Contrato B2B activo |
| `admin` | Ver todo, moderar, aprobar instructores, gestionar revenue | Solo dueño + staff |

---

## 2. Revenue share

| Quién | % por venta en marketplace | Condición |
|---|---|---|
| Instructor | 70% | Curso en catálogo activo, quality gate pasado |
| Whetzy | 30% | Cubre infraestructura, motor, pagos, soporte |

**Comparativa con competidores:**
- Udemy: 25-37% para instructor (revenue share cae si Udemy pone el curso en promoción)
- Teachable: 0% comisión pero cobra $99+/mes por plataforma
- Gumroad: 10% flat
- **Whetzy: 70% fijo, sin cargos de plataforma para el instructor**

**Pago:** Mensual, el día 15, mínimo $50 acumulado. **Rail elegido por el instructor**
(ADR-36): Stripe Connect donde exista; **USDC en Solana** (fee ≈ $0,001, liquidado
como stablecoin, nunca otro token) o Wise donde Stripe Connect no opere (la mitad de
LATAM). La fiscalidad es del instructor (KYC en 28.0; marco en 21.1). Whetzy nunca
custodia cripto ni mantiene wallet con saldo operativo.

---

## 3. Quality gate para contenido de instructores

Todo contenido de instructor pasa el mismo §7 del CATALOGO_MAESTRO.md:

| Criterio | Valor mínimo | Verificado por |
|---|---|---|
| Preguntas por skill | ≥ 15 | `check_question_bank.py` |
| Preguntas ejecutables | ≥ 15% donde el runtime lo permita | ídem |
| Términos de glosario | ≥ 36 por track | `check_docs.py` |
| Lecciones con contenido | 100% (no esqueleto) | `check_docs.py` |
| Licencia del material fuente | Solo [reusar] o original del instructor | `check_source_licenses.py` |
| Sin dumps de certificaciones | 0 preguntas copiadas literalmente | revisión manual |
| Idioma | Coherente con segmento declarado (ES o EN) | revisión manual |

**Flujo de aprobación:**
1. Instructor sube contenido vía panel
2. Quality gate automático corre → pasa o falla con errores específicos
3. Si pasa → revisión manual por admin (24-48h)
4. Si aprobado → publicado en marketplace
5. Si rechazado → feedback específico al instructor + plazo para corregir

---

## 4. Panel del instructor

### Vista principal
- Revenue acumulado (mes actual + histórico)
- Próximo pago y fecha
- Cursos activos: estudiantes inscritos, completion rate, rating promedio
- Alertas: quality gate issues, reviews nuevas, mensajes de estudiantes

### Código de instructor (ADR-35)
- Cada instructor tiene un código `PROF-<nombre>-<pct>` (`ECONOMIA.md` §4): da un
  descuento a sus alumnos en **su** curso y atribuye esas ventas al instructor en su
  panel. Canje solo en web. No da créditos al instructor: su incentivo es visibilidad
  (ranking por completion rate) y revenue.
- Los alumnos pueden pagar cursos del marketplace también con créditos (`ECONOMIA.md`
  §2.3): el 70 % del instructor se liquida al valor nominal desde la bolsa de
  marketing de Whetzy, nunca del alumno.

### Creación de contenido
- Editor web para lecciones (Markdown + preview)
- Upload de preguntas en formato JSON (template provisto)
- Preview del curso como estudiante antes de publicar
- Historial de versiones

### Métricas por curso
- Estudiantes totales / activos (últimos 30 días)
- Completion rate
- Nota media del BKT por concepto (dónde fallan más los estudiantes)
- Reviews y ratings
- Revenue total y por mes

---

## 5. Protección de instructores y estudiantes

### Para instructores
- **Contenido propio:** El instructor mantiene los derechos de su material
- **Exclusividad NO requerida:** Pueden vender el mismo contenido en otras plataformas
- **Datos:** Whetzy no comparte datos de los estudiantes del instructor con terceros
- **Contrato:** Terms of Service de instructor firmado digitalmente al activar el rol

### Para estudiantes
- **Reembolso:** 7 días si no han completado más del 30% del curso
- **Acceso de por vida** al contenido comprado (incluso si el instructor sale de la plataforma)
- **Quality garantizada:** Todo curso pasó el quality gate — si falla post-publicación, Whetzy lo retira y reembolsa

---

## 6. Moderación

### Qué se modera
- Contenido que viola ADR-11 (fuentes ilegales o de pago pirateado)
- Contenido que copia dumps de certificaciones
- Contenido ofensivo, discriminatorio o inapropiado
- Contenido factualmente incorrecto en conceptos críticos

### Cómo
- Reporte de estudiante → admin review en 48h
- Revisión periódica aleatoria de 10% del contenido nuevo
- BKT como detector: si muchos estudiantes fallan los mismos conceptos del mismo curso,
  puede indicar contenido deficiente → flag para revisión

---

## 7. Serie 28 — Implementación técnica

| Tarea | Descripción |
|---|---|
| 28.0 | Schema DB: tablas `instructor_profiles`, `marketplace_courses`, `course_purchases`, `instructor_payouts` |
| 28.1 | API endpoints: CRUD cursos instructor, upload contenido, métricas; código de instructor (29.4) |
| 28.2 | Quality gate pipeline: `scripts/instructor_quality_gate.py` integrado en upload |
| 28.3 | Panel de instructor: React pages con rol-guard `instructor` |
| 28.4 | Marketplace público: catálogo filtrable, ratings, preview de lección |
| 28.5 | Checkout: Stripe/Paddle para compra de cursos de instructor, split de revenue automático |
| 28.6 | Panel de admin: aprobación de cursos, gestión de payouts, moderación |
| 28.7 | Payouts automáticos: job mensual día 15; Stripe Connect, USDC en Solana o Wise según el instructor (ADR-36, con 29.9) |

---

## 8. Lanzamiento del marketplace

**Fase 1 (en paralelo con Serie 24):** Reclutar 5 instructores beta invitados.
Criterios: Python/AI practitioners con audiencia existente (YouTube, LinkedIn, Twitter).
Oferta: 70% revenue share + badge "Instructor Fundador" + visibilidad prioritaria.

**Fase 2 (post Serie 28 DONE):** Apertura pública del formulario de solicitud.
Objetivo: 20 instructores activos con al menos 1 curso publicado en mes 3.

**Fase 3 (año 1):** 50+ instructores, 100+ cursos en marketplace, generando
$2,000-5,000/mes en revenue share total (= $600-1,500/mes para Whetzy).
