/**
 * Plan figures the UI shows and the backend enforces (ADR-49).
 * `backend/tests/test_constantes_planes.py` fails if these drift from `settings`.
 */

/** Tutor explanations per UTC day on Pro (`plus`); Pro Max has no cap. */
export const TUTOR_DAILY_LIMIT_PRO = 20;

/** One-time price of a certification's certifying exam, retakes included. */
export const CERTIFICATION_PRICE_USD = 39.99;
