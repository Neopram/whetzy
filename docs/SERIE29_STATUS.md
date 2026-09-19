# Serie 29 - Economía Cerrada: Estado de Implementación (Sesión bj)

## COMPLETADO: 29.0-29.3 (Backend Core)

### ✅ 29.0 - Credit Ledger Schema
**Archivos:** 
- `backend/app/models/economy.py` (186 líneas)
- `backend/alembic/versions/20260919_1500_v0w1x2y3z4a5_economy_credits_referrals.py`

**Tablas creadas:**
- credit_ledger (inmutable, FIFO)
- referral_codes (permanente por user)
- referrals (tracking)
- promo_codes
- promo_code_redemptions
- credit_expense_caps

### ✅ 29.1 - Credit Service
- `backend/app/services/economy.py` (240 líneas)
- Métodos: grant_credits, get_balance, spend_fifo, expire_old_credits
- Idempotencia probada

### ✅ 29.2 - Grifos/Sumideros
- `content/economy/credits.json` (tabla de precios)
- `backend/app/api/v1/endpoints/economy.py` (5 endpoints)

### ✅ 29.3 - Referral Service
- Código permanente, activación, tracking

### ✅ Tests
- `backend/tests/unit/test_economy_services.py` (8 tests)

## FALTA INTEGRAR

1. Registrar router en `main.py`:
   ```python
   from app.api.v1.endpoints import economy
   app.include_router(economy.router)
   ```

2. Exportar modelos en `app/models/__init__.py`

3. Ejecutar migración local:
   ```bash
   cd backend && python -m alembic upgrade head
   ```

## TODO: Sesión Siguiente

| ID | Tarea | Estado | Prioridad |
|----|-------|--------|-----------|
| 29.4 | Códigos: tipos, topes, caducidad | TODO | 1 |
| 29.5 | Antifraude (dispositivo/IP/listas) | TODO | 2 |
| 29.6 | Admin integration | TODO | 2 |
| 29.7 | Job: reactivación | TODO | 3 |
| 29.8 | UI Wallet (React, 4 tabs) | TODO | 1 |
| 29.9 | USDC | BLOCKED (H.19) | — |
| 29.10 | Open Badges | BLOCKED (17.2) | — |
| 29.11 | Cláusulas legales | TODO | 3 |
| 29.12 | Scorecard | TODO | 4 |

## Criterios de Aceptación

✅ Schema migrable  
✅ FIFO ledger  
✅ Balance = SUM(ledger)  
✅ Idempotency  
✅ Referral codes  
⏳ UI Wallet  
⏳ Admin panel  
⏳ Cláusulas legales  
