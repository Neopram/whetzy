# Serie 29: Economía Cerrada — Planificación

**Fecha:** 2026-09-19  
**Estado:** TODO | Depende H.26 ✅, H.29 ⏳  
**Tamaño:** 13 tareas  
**Crítica:** Monetización principal (después de IAP/Paddle)

---

## § 1. Reglas de Créditos (29.0 — Priority 0)

### Estructura ECONOMIA.md §1 (Usuario Confirmó H.26)

**Grifos (Ingresos de créditos al sistema):**
1. **Pagos de suscripción** (plan Pro/Plus)
   - Pro: 100 créditos/mes = €10/mes
   - Plus: 300 créditos/mes = €30/mes
   - Bilingüe (EUR y USD según región)

2. **Sponsors de tracks** (empresas pagan por visibility)
   - Ejemplo: "Python Fundamentals por Google"
   - Ingresos en pool de créditos gratis

3. **Grants externos** (Solana Foundation, etc.)
   - H.28: Solicitar grant Solana
   - Depositar en pool de créditos

**Sumideros (Gastos de créditos del usuario):**
1. **Créditos gratis iniciales** (retención)
   - Onboarding: 5 créditos (registrate y prueba)
   - D7 retention bonus: +10 créditos si completó placement
   - D30 retention: +25 créditos si activo
   - Monthly drip: 5 créditos si subscriber
   
2. **Referidos (K-factor de crecimiento)**
   - Invitas a amigo → ambos reciben 10 créditos
   - Si amigo compra Pro → 50 créditos de bonus
   - Escala: K-factor = 1.2 (sostenible)

3. **Instructor payouts** (de la pool)
   - 70% de ingresos de curso → instructor
   - 30% × 10 créditos = 3 créditos al sistema
   - (O según rail en 21.2)

**Tasa de Canje:**
- 1 crédito = €0.10 (o USD 0.11)
- Mínimo canje: 100 créditos = €10
- Máximo/mes: sin límite (pero auditado)

---

## § 2. Modelo de Datos (29.1 Backend)

### Tablas requeridas

```sql
-- Ledger de transacciones de créditos
CREATE TABLE credit_transactions (
    id UUID PRIMARY KEY,
    user_id UUID FOREIGN KEY,
    amount INTEGER (créditos, puede ser negativo),
    transaction_type ENUM('grant', 'purchase', 'referral', 'instructor_payout', 'canje', 'expire'),
    reason TEXT,
    created_at TIMESTAMP,
    expires_at TIMESTAMP (NULL si no expira),
    INDEX (user_id, created_at)
);

-- Saldo actual (desnormalizado para velocidad)
CREATE TABLE credit_balance (
    user_id UUID PRIMARY KEY,
    total_credits INTEGER,
    pending_credits INTEGER (esperando confirmación),
    last_updated TIMESTAMP,
    INDEX (total_credits DESC) -- top earners
);

-- Referidos y K-factor
CREATE TABLE referral_links (
    id UUID PRIMARY KEY,
    from_user_id UUID FOREIGN KEY,
    referral_code VARCHAR(12) UNIQUE,
    to_user_id UUID FOREIGN KEY (NULL si no convertido),
    created_at TIMESTAMP,
    converted_at TIMESTAMP (NULL si pending),
    credit_awarded BOOLEAN (ambos usuarios: reciben créditos)
);

-- Canjes de créditos a suscripciones/features
CREATE TABLE credit_redemptions (
    id UUID PRIMARY KEY,
    user_id UUID FOREIGN KEY,
    credits_used INTEGER,
    redeemed_for ENUM('subscription_pro_month', 'subscription_plus_month', 'featured_certificate', 'private_lesson'),
    status ENUM('pending', 'confirmed', 'expired'),
    created_at TIMESTAMP,
    expires_at TIMESTAMP
);
```

### Endpoints requeridos

```
POST /api/v1/economy/transactions — audit log (admin only)
GET /api/v1/economy/balance — mi saldo + histórico
POST /api/v1/economy/redeem/{type} — canjear créditos por feature
GET /api/v1/referrals/link — mi código referido
POST /api/v1/referrals/accept/{code} — aceptar referido (con bonus)
GET /api/v1/referrals/earnings — mis referidos y earnings
```

---

## § 3. UI Wallet (29.2 Frontend)

### CreditWallet.tsx (Componente principal)

**Tabs:**
1. **Saldo** (mostrando)
   - Total créditos con visual progress bar
   - Próximas expiraciones (si aplica)
   - Bonificaciones pendientes (si hay)

2. **Histórico** (todas las transacciones)
   - Filtro por tipo (compras, referidos, expiración)
   - Sorting por fecha descending
   - Bilingual ES/EN

3. **Canje** (marketplace de features)
   - "Compra 1 mes Pro por 100 créditos"
   - "Destaca tu certificado por 50 créditos"
   - Status: enabled/disabled si balance suficiente

4. **Referidos** (K-factor)
   - Mi código compartible (copy to clipboard)
   - Lista de personas invitadas
   - Créditos ganados por cada referido
   - Total earnings

### Diseño

- Card-based layout (responsive mobile-first)
- Color: oro/amarillo para créditos (visual diferente a suscripciones)
- Animaciones: +X créditos confetti on purchase
- i18n: ~25 claves ES/EN

---

## § 4. Integración Gamificación (29.8 con 24.6)

**Conexiones con racha/logros:**

1. **Racha x Créditos**
   - Día 7 racha → +5 créditos bonus
   - Día 30 racha → +25 créditos bonus
   - Día 100 racha → +100 créditos (feature especial)

2. **Logros → Créditos**
   - Completar track → 50 créditos
   - Top 10 liga → 100 créditos (semanal)
   - 1000 preguntas correctas → 200 créditos (one-time)

3. **Duelos → Créditos**
   - Ganar duelo → 2 créditos
   - Ganar 10 seguidas → 50 créditos bonus
   - Campeón liga → 500 créditos (mensual)

---

## § 5. Legal y Compliance (29.11)

### Textos en ToS/Privacy (H.20 debe revisar)

**Cláusula 1: Créditos no son dinero**
- "Créditos son moneda de plataforma, no equivalente directo a dinero legal"
- "No transferible entre usuarios"
- "Expiran si no se usan en 12 meses" (parámetro configurable)

**Cláusula 2: Referidos sin phishing**
- "No solicitar datos personales de referidos"
- "Solo compartir código, no emails masivos"
- "Créditos por referido: 10 + 50 si convierte"

**Cláusula 3: Instructor payouts**
- "70% de ingresos tras comisión de plataforma"
- "Payouts mensuales, mínimo €50"
- "Impuestos responsabilidad del instructor" (depende H.29 entidad)

---

## § 6. Testing (29.1-29.2)

### Pytest Suite
```
tests/integration/test_credit_system.py
├─ test_credit_grant (onboarding)
├─ test_referral_bonus (K-factor)
├─ test_expiration (after 12 months)
├─ test_insufficient_balance (no créditos)
├─ test_redemption_subscription (canje)
└─ test_instructor_split (70/30)
```

### E2E (Playwright)
- User A registra → recibe 5 créditos ✅
- User A invita a User B con código
- User B registra con código → ambos reciben 10 créditos ✅
- User B compra Pro (€10) → User A recibe 50 créditos ✅
- User A canjea 100 créditos por 1 mes Pro ✅

---

## § 7. Timeline

**Semana 1 (29.0-29.1):**
- Reglas finalizadas (hoy)
- Modelos y migrations
- Endpoints básicos (GET balance, POST transaction)

**Semana 2 (29.2-29.3):**
- UI wallet (React)
- Canje workflow
- Testing suite

**Semana 3 (29.6-29.8):**
- Atribución de referidos (con 28.7)
- Integración gamificación
- Legal review (H.20)

**Semana 4+ (29.10-29.11):**
- Open Badges 3.0 (opcional, H.27)
- Cláusulas finales en ToS
- Producción (H.SEED)

---

## § 8. Blockers y Dependencias

| Blocker | Crítica | Impacto |
|---|---|---|
| **H.29 Decisión Fiscal** | 🔴 PRI 0 | Instructor split % (depende rail) |
| **H.20 Revisión Legal** | 🔴 PRI 0 | Cláusulas de créditos + referidos |
| **28.7 Payouts** | 🟡 PRI 1 | Integración con instructor earnings |
| **24.6 Gamificación** | 🟡 PRI 1 | Bonus de racha + logros |

---

**Próxima acción:** Esperar H.29 usuario input (días Grecia) → bifurcación instructor split %

