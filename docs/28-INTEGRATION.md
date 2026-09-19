# Serie 28: Instrucciones de Integración

**Último actualizado**: 2026-09-19  
**Status**: Scaffold 28.0 - Pendiente integración

---

## Backend Integration

### 1. Registrar modelos en `app/models/__init__.py`

```python
from app.models.instructor import (
    Instructor,
    InstructorCourse,
    InstructorEnrollment,
    InstructorPayout,
)

__all__ = [
    ...existing models...,
    "Instructor",
    "InstructorCourse", 
    "InstructorEnrollment",
    "InstructorPayout",
]
```

### 2. Registrar routes en `app/api/v1/routes.py` o `app/main.py`

```python
from app.api.v1.endpoints import instructor

# En el setup de FastAPI:
app.include_router(
    instructor.router,
    prefix="/api/v1/instructor",
    tags=["instructor"],
)
```

### 3. Crear usuario con rol `instructor` (Opcional, Schema Update)

En `app/models/user.py`, se recomienda agregar valores válidos para `role`:

```python
role: Mapped[str] = mapped_column(
    String(32), 
    default="user", 
    nullable=False,
    # Validar en: ["user", "instructor", "admin"]
)
```

### 4. Crear migración Alembic (Esperar H.29)

```bash
# NO ejecutar aún; esperar confirmación de H.29
cd backend
alembic revision --autogenerate -m "add instructor marketplace tables"
```

---

## Frontend Integration

### 1. Importar i18n instructor keys

En `frontend/src/i18n.ts` o en tu loader de i18n:

```typescript
import esInstructor from './i18n/es/instructor.json'
import enInstructor from './i18n/en/instructor.json'

// Merge con recursos existentes
const resources = {
  es: {
    translation: {
      ...existingES,
      instructor: esInstructor.instructor,
    }
  },
  en: {
    translation: {
      ...existingEN,
      instructor: enInstructor.instructor,
    }
  }
}
```

### 2. Agregar ruta en App.tsx o router

```typescript
import InstructorScreen from './pages/InstructorScreen'

// En tu router (Reacts Router v6 recomendado):
<Route path="/instructor" element={<InstructorScreen />} />
```

### 3. Agregar enlace en navegación (opcional)

```typescript
// En tu navbar/menu
{user?.role === 'instructor' && (
  <Link to="/instructor">{t('instructor.title')}</Link>
)}
```

---

## API Endpoints (28.0 Scaffold)

| Method | Endpoint | Status | Response |
|--------|----------|--------|----------|
| POST | `/api/v1/instructor/profile` | 501 | NotImplemented |
| GET | `/api/v1/instructor/profile/{id}` | 200 | Mock profile |
| POST | `/api/v1/instructor/courses` | 501 | NotImplemented |
| GET | `/api/v1/instructor/courses` | 200 | Mock courses |
| GET | `/api/v1/instructor/analytics` | 200 | Mock analytics |
| GET | `/api/v1/instructor/payouts` | 501 | NotImplemented (H.29) |

---

## Next Steps (28.1+)

### Week 2 (28.1: Core Logic)
1. Implementar `POST /instructor/profile` con DB persistence
2. Implementar `POST /instructor/courses` con validación de precio
3. Implementar `GET /instructor/analytics` con queries reales
4. Frontend: Conectar forms a APIs (reemplazar mock)

### Week 3+ (28.2+: Payouts, depende H.29)
1. Implementar `GET /instructor/payouts` una vez H.29 apruebe rail
2. Integrar Stripe/Paddle SDK
3. Crear background job para procesar payouts (celery/APScheduler)
4. Frontend: Payouts tab operativo

---

## Testing Checklist

- [ ] Backend models compile (pytest)
- [ ] Endpoints stubbed and return correct status codes
- [ ] Frontend components render without errors
- [ ] i18n keys resolve in both ES and EN
- [ ] Responsive design works on mobile (Capacitor)
- [ ] No linting errors (eslint, black, mypy)

---

## Known Issues / Todos

| Issue | Status | Owner | Timeline |
|-------|--------|-------|----------|
| Payout logic stub (501) | Open | TBD | H.29+ (W44) |
| User role validation | Open | Auth Lead | W41 |
| DB migrations | Blocked | Backend | H.29 sign-off |
| Stripe/Paddle decision | Blocked | Finance | EOD W39 |
