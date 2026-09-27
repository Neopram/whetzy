/**
 * Plan figures the UI shows and the backend enforces (ADR-49).
 * `backend/tests/test_constantes_planes.py` fails if these drift from `settings`.
 */

/** Tutor explanations per UTC day on Pro (`plus`); Pro Max has no cap. */
export const TUTOR_DAILY_LIMIT_PRO = 20;

/** One-time price of a certification's certifying exam, retakes included. */
export const CERTIFICATION_PRICE_USD = 39.99;

/** Plan Free (ADR-50a, 39.4): new questions and lessons per UTC day. Enforced only
 *  while `FREE_DAILY_QUOTA_ENABLED` is on in the backend (off until billing opens). */
export const FREE_DAILY_NEW_QUESTIONS = 30;
export const FREE_DAILY_LESSONS = 5;
