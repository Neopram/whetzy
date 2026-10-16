# A/B Testing Framework — 24.14

## Overview

Whetzy uses a deterministic, user-stable A/B testing framework for experiments. Each user gets assigned to a variant (A or B) based on a hash of their ID, ensuring they see the same variant every session.

## How It Works

> Status: only the model, MD5 assignment, `GET /api/v1/experiments/flags` and the `useExperimentFlags`/`useVariant` hooks exist. There is no admin endpoint or UI for experiments, no χ² stats and no `conclusion` field: everything below that mentions the admin panel is planned design, not built.

### 1. Backend: Deterministic Assignment

When a user first enters an active experiment:
```python
variant = await get_user_variant(db, experiment_id, user_id)
# Returns: "A" or "B" deterministically based on MD5(experiment_id:user_id) % 2
```

- Hash of `experiment_id:user_id` determines variant
- Result is cached in `experiment_assignments` table
- Same user always sees same variant, across sessions

### 2. Frontend: Conditional Rendering

```typescript
const { flags } = useExperimentFlags()
const ctaColor = flags['landing_cta'] === 'A' ? 'blue' : 'green'

return <button style={{ backgroundColor: ctaColor }}>Start Free</button>
```

- Hook fetches flags on mount from `/api/v1/experiments/flags`
- Rendered component varies based on variant

### 3. Admin: Metrics

In admin panel (22.1), under **Experiments** tab:
```
Experiment: landing_cta
├─ Variant A (Blue): 142 users, 18 signups, 12.7% conversion
├─ Variant B (Green): 156 users, 21 signups, 13.5% conversion
└─ Stats: χ² p-value = 0.42 (not significant)
```

## First Experiment: Landing CTA Color

### Setup

1. **Create experiment via admin:**
   - Name: `landing_cta`
   - Variant A: "Blue (#3B82F6)"
   - Variant B: "Green (#10B981)"
   - Hypothesis: "Green increases CTR by 5%"

2. **Start experiment:**
   - Status: `active`
   - Started: *(example — the ledger says this experiment (24.14) was never imported, so it
     never ran; corrected 2026-09-25)*

3. **Implement on LandingScreen:**
   ```typescript
   export function LandingScreen() {
     const variant = useVariant('landing_cta', 'A')
     const ctaColor = variant === 'A' ? '#3B82F6' : '#10B981'
     
     return (
       <button style={{ backgroundColor: ctaColor }}>
         EMPEZAR A APRENDER
       </button>
     )
   }
   ```

### Metrics to Track

- **Sign-up rate:** Users who start signup after seeing CTA
- **Completion rate:** Users who finish signup (not abandon)
- **Landing-to-quiz:** Time from landing to first quiz question
- **Conversion:** Sign-up completion per variant

### Duration & Sample Size

- **Minimum duration:** 7 days (to capture weekly patterns)
- **Target sample:** 300 users per variant (600 total)
- **Significance level:** p < 0.05

### Result Recording

Once experiment ends:

1. **Admin:** Stop experiment (status → `ended`, set `ended_at`)
2. **Record result:** In experiment record, add `conclusion`:
   ```
   {
     "winner": "B",  // or "none" if inconclusive
     "effect_size": 1.5,  // % improvement
     "p_value": 0.031,
     "interpretation": "Green CTA increased conversion by 1.5%, p=0.031"
   }
   ```
3. **Deploy winner:** Roll out winning variant to 100% of users

## Database Schema

### Experiment
```sql
CREATE TABLE experiments (
  id UUID PRIMARY KEY,
  name VARCHAR(128) UNIQUE,
  status VARCHAR(20),  -- 'draft', 'active', 'ended'
  variant_a_label VARCHAR(100),
  variant_b_label VARCHAR(100),
  hypothesis TEXT,
  started_at TIMESTAMP,
  ended_at TIMESTAMP
);
```

### ExperimentAssignment
```sql
CREATE TABLE experiment_assignments (
  id UUID PRIMARY KEY,
  experiment_id UUID REFERENCES experiments,
  user_id UUID REFERENCES users,
  variant VARCHAR(10),  -- 'A' or 'B'
  UNIQUE(experiment_id, user_id)
);
```

## Runbook: Create New Experiment

### Step 1: Create experiment record
```bash
curl -X POST http://localhost:8000/api/v1/admin/experiments \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "onboarding_flow",
    "variant_a_label": "3 questions",
    "variant_b_label": "5 questions",
    "hypothesis": "Longer onboarding improves retention"
  }'
```

### Step 2: Code frontend variant
```typescript
const variant = useVariant('onboarding_flow', 'A')
const questionCount = variant === 'A' ? 3 : 5
```

### Step 3: Start experiment via admin UI
- Set status → active
- Set started_at → now

### Step 4: Monitor in admin
- Dashboard shows real-time counts and stats
- Pull results after 7+ days

## Determinism Proof

Test validates that:
```
hash(exp_id="abc", user_id="123") % 2 → always same result
```

Running `pytest tests/test_experiments.py::test_deterministic_variant_assignment` confirms.
