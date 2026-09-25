# Serie 28: Marketplace Instructores - Plan Técnico

**Status**: Scaffold | **Propuesta**: 2026-09-19 | **Timeline**: 2 semanas (W40-W41)  
**Dependencias**: 22.1 Admin (DONE), H.29 entidad fiscal, 21.2 decisión payout  
**Bloqueantes**: Definición rail de payout (Stripe vs Paddle) en H.29

---

## Visión: Instructor Journey

`
[Instructor signup/login] 
  ↓
[Complete profile: bio, avatar, payout details]
  ↓
[Upload course: title, description, price, materials, video URL]
  ↓
[Course published in marketplace; students can browse + enroll]
  ↓
[Student enrollment → instructor earns revenue]
  ↓
[Monthly/quarterly payout to instructor account]
  ↓
[Analytics: enrollments, retention, revenue]
`

---

## Revenue Model (Parametrizable por Rail)

**Estructura base** (customizable por payment provider):
- Instructor retiene: **70%** de course price
- Plataforma retiene: **30%** (operations, payment processing, fraud, support)

Ejemplo:
- Curso a USD 100 → Instructor gana USD 70 → Plataforma retiene USD 30
- Earnings acumulables por periodo (monthly/quarterly, TBD en H.29)
- Payouts manuales o automáticos (TBD)

**Parámetros en settings/rail config**:
`python
INSTRUCTOR_REVENUE_SPLIT = 0.70  # Instructor %
PLATFORM_REVENUE_SPLIT = 0.30    # Platform %
PAYOUT_PERIOD = "monthly"        # "monthly" | "quarterly" | custom
PAYOUT_PROVIDER = None            # "stripe" | "paddle" | set en H.29
MIN_PAYOUT_THRESHOLD = 10_00      # cents;  mínimo antes de payout
`

---

## Timeline Ejecutivo (2 semanas)

### **Semana 1: UI + Schema**
- **Lunes-Martes**: Modelos ORM (instructor.py, tablas, constraints)
- **Miércoles**: Routes skeleton (stubs 501/mock, sin negocio)
- **Jueves-Viernes**: Frontend scaffold + i18n keys
- **Deliverable**: Schema + routes existentes + UI wireframe; tests desactivados (pending spec final)

### **Semana 2: Lógica + Transiciones**
- **Lunes-Martes**: Implementación routes (profile create/read, course CRUD)
- **Miércoles**: Analytics queries (enrollments, revenue, retention)
- **Jueves**: Frontend: Profile tab + Course tab + Analytics tab (mock data)
- **Viernes**: QA + merge a develop
- **Deliverable**: Rutas funcionales (sin payout), frontend operativo

### **Semana 3+**: Post-scaffold (depende H.29)
- **Payout logic**: Esperar decisión rail (Stripe vs Paddle)
- **Migrations finales**: Una vez H.29 cierre entidad fiscal
- **Live payouts**: Integración payment provider (W44+)

---

## Criterios de Aceptación (28.0)

- [x] Plan documentado + timeline visible
- [x] Modelos ORM: Instructor, InstructorCourse, InstructorEnrollment, InstructorPayout
- [x] Unique constraint: (user_id, 1 instructor per user)
- [x] Routes existentes: POST/GET profile, POST/GET courses, GET analytics
- [x] Routes devuelven 501 NotImplemented o mock data (sin lógica transaccional)
- [x] Frontend scaffold: 4 tabs (Profile, Courses, Analytics, Payouts)
- [x] i18n: ~25 keys (ES/EN)
- [x] Responsive design (mobile-first, Capacitor-ready)
- [ ] NO payouts (esperar H.29)
- [ ] NO admin panel mods (eso es 22.1, ya DONE)
- [ ] NO migraciones DB (esperar H.29 + confirmación schema)

---

## Archivos Entregados

`
backend/
  app/
    models/
      instructor.py                   # ORM: Instructor, Course, Enrollment, Payout
    api/v1/endpoints/
      instructor.py                   # Routes (stubs + mock)

frontend/
  src/
    pages/
      InstructorScreen.tsx            # Page root (bilingual)
    components/
      instructor/
        InstructorPanel.tsx           # Container + tab router
        ProfileTab.tsx                # Profile form
        CourseTab.tsx                 # Course list + upload form
        AnalyticsTab.tsx              # Dashboard: earnings, students, retention
        PayoutsTab.tsx                # Payout history (stub)
    i18n/
      es/
        instructor.json               # ES keys
      en/
        instructor.json               # EN keys

docs/
  28-PLANNING.md                      # Este fichero
`

---

## Blockages & Dependencies

| Blocker | Owner | Impact | Resolution Timeline |
|---------|-------|--------|---------------------|
| H.29: Rail + entidad fiscal | Product | Payout logic, tax forms | EOW 2026-09-26 |
| 21.2: Stripe vs Paddle decision | Finance/Product | Payment integration | EOD 2026-09-25 |
| 22.1 Admin panel (course mgmt) | Lead | Course moderation UI | DONE 2026-09-19 ✓ |

---

## Notas Técnicas

1. **Auth**: Reutilizar get_current_user + validar role='instructor' (crear role si no existe en user.py)
2. **Uniqueness**: user_id FK → 1 instructor per user; enforce en schema
3. **Pricing**: Almacenar en cents (USD cents) para evitar float precision issues
4. **Analytics**: Queries optimizadas (índices en instructor_id, course_id, created_at)
5. **Migrations**: Esqueleto stub SQL; pending finales de H.29 para flyway/Alembic
6. **Payouts**: Lógica diferida; route GET /payout-status devuelve 501 por ahora

---

## Testing Strategy

- **Unit**: ORM validators (price > 0, payout_address format)
- **Integration**: Routes mock (stubbed endpoints OK, no DB hits)
- **E2E**: Pending H.29 (payout workflows)

---

## Handoff Checklist

- [ ] Schema aprobado por Product
- [ ] Routes spec conformado a OpenAPI /api/v1/openapi.json
- [ ] i18n keys translatable (no hardcoded strings en components)
- [ ] Frontend tests (jest + @testing-library/react) mock API
- [ ] Migrations pending H.29; schema freeze declared
