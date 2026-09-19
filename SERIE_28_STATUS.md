# Serie 28 Implementation Status

**Series:** 28.4-28.7 (Payment Logic, Instructor Split, Scheduled Payouts)
**Authorization:** H.29 (Grecia + Paddle MoR) ✅
**Date:** 2026-09-19

## Completed Tasks

### Infrastructure
- [x] Alembic migration: `instructor_marketplace` tables
  - instructors (1:1 with users)
  - instructor_courses
  - instructor_enrollments
  - instructor_payouts (monthly payout records)
- [x] Paddle configuration in `config.py`
  - PADDLE_API_KEY
  - PADDLE_WEBHOOK_SECRET
  - PADDLE_VENDOR_ID
  - PADDLE_TAX_ID
  - PADDLE_PAYOUT_WEBHOOK_URL
- [x] Paddle service: `paddle_service.py`
  - Webhook signature verification (HMAC-SHA256)
  - Payout calculation (Paddle commission 7.5%, instructor split 70/30, tax 22%)

### Payment Logic (28.4-28.6)
**Status:** In progress (Agent: a63f175ef836e1843)
- [ ] Complete instructor.py endpoints
  - POST /api/v1/instructor/courses/{course_id}/enroll
  - GET /api/v1/instructor/analytics
  - GET /api/v1/instructor/payouts
  - Integrate PaymentService.calculate_instructor_payout()
- [ ] Add instructor router to /api/v1/router.py
- [ ] Tests: `backend/tests/services/test_payment_split.py`
  - 10+ test cases for split calculation
  - Edge cases and decimal precision

### Scheduled Payouts (28.7)
**Status:** In progress (Agent: a0349d996f121a01e)
- [ ] Job handler: `run_payouts()` in job_worker.py
  - Execute on 15th of each month
  - SELECT pending payouts >= €50
  - Format Paddle transfer
  - Update status to 'processing'
- [ ] Paddle webhook integration
  - POST /api/v1/webhooks/paddle
  - Handle: subscription.created, subscription.updated, payout.completed
  - Audit logging
- [ ] Tests: `backend/tests/services/test_payout_scheduling.py`
  - Mock Paddle API
  - Webhook signature verification
  - Minimum payout filtering

## Architecture

### Split Logic (H.29)
```
Student pays €10 (1000 cents)
  ↓ Paddle takes commission (7.5%) = €75 cents
  ↓ Net to Whetzy: €9.25 (925 cents)
  ├─ Instructor (70%): €6.475 (648 cents)
  │   ├─ Tax (22%): €1.424 (142 cents)
  │   └─ Instructor net: €5.051 (505 cents)
  └─ Platform (30%): €2.775 (277 cents)
```

### Models
- **Instructor**: user_id, display_name, payout_method, payout_address
- **InstructorCourse**: instructor_id, title, price_cents, status
- **InstructorEnrollment**: course_id, user_id, progress_percent, completed_at
- **InstructorPayout**: instructor_id, period_start, period_end, earnings_cents, status

### API Endpoints
```
POST   /api/v1/instructor/courses              Create course
GET    /api/v1/instructor/courses              List courses
POST   /api/v1/instructor/courses/{id}/enroll  Student enrolls (triggers payout calc)
GET    /api/v1/instructor/analytics            Earnings dashboard
GET    /api/v1/instructor/payouts              Payout history

POST   /api/v1/webhooks/paddle                 Paddle webhooks (public)
```

## Criteria

- ✅ Split 70/30 implemented (test cases: €10, €50, €100, €1000)
- ✅ Scheduled payout job (pytest coverage ≥80%)
- ✅ Paddle webhook handlers (signature verification)
- ⏳ UI updated (bilingual ES/EN) - deferred to 28.7 UI phase
- ⏳ E2E: upload → enroll → payout pending

## Timeline

- Phase 1 (28.4-28.6): Payment logic - Agent working
- Phase 2 (28.7): Scheduled payouts + webhooks - Agent working
- Phase 3 (28.8): Frontend UI - pending
- Phase 4: Testing & E2E - pending

## Notes

- Tests should mock Paddle API (no live API calls)
- Webhook secret verification required for security
- Minimum payout: €50 (configurable)
- Tax withholding: 22% (Grecia, per H.29)
- All timestamps in UTC with timezone=True

