import { test, expect } from '@playwright/test';
import { registerUser, uniqueUsername } from './helpers';

/**
 * Track final exam and certificate (17.2), end to end against a real server.
 *
 * The integration tests prove the blueprint, the clock, the grading and the
 * certificate are right. They say nothing about whether a learner can reach any
 * of it. This spec walks the path: catalogue -> a course that is not a
 * certification rehearsal -> its final exam -> a real question with a running
 * clock.
 *
 * It deliberately stops short of sitting all twenty questions. Answering a full
 * paper through the UI would take minutes of wall clock for no extra signal:
 * the grading, the pass mark, the certificate and the per-skill report are
 * covered by `backend/tests/integration/test_track_exam.py`, against the same
 * endpoints this screen calls. What only an e2e run can tell us is that the
 * button exists, the attempt is really committed (a flush alone would survive
 * SQLite and die on Postgres) and the questions paint.
 */
test.describe('track final exam', () => {
  test('reaches the final exam of a course and starts a timed sitting', async ({ page }) => {
    const username = uniqueUsername('e2e_final_');
    await registerUser(page, { username, displayName: 'E2E Final' });

    await page.getByRole('button', { name: 'Rutas' }).click();

    // track01 is a course, not a certification rehearsal, so it is the final
    // exam that should be offered here and not the mock.
    const cta = page.getByRole('button', { name: /Examen final del curso|Course final exam/ });
    await expect(cta).toBeVisible({ timeout: 15_000 });

    // The blueprint is on the button before anything is committed to: the
    // learner should not discover the exam is fifty questions long by starting
    // it. These numbers come from the server, not from a constant in the page.
    await expect(cta).toContainText(/\d+/);

    await cta.click();

    // The intro states the pass mark, which is the part a learner most needs
    // before deciding.
    // Anchored on the pass-mark line itself: a bare /70/ also matches every
    // «… · 70%» unlock note on the Tracks screen that is still animating out.
    await expect(page.getByText(/(se aprueba con|pass mark) 70/i)).toBeVisible({ timeout: 10_000 });

    await page.getByRole('button', { name: /EMPEZAR EXAMEN|START EXAM/ }).click();

    // A question and a running clock. If the attempt had not been committed by
    // the endpoint, this is where it would fail on Postgres.
    await expect(page.getByRole('radiogroup')).toBeVisible({ timeout: 30_000 });
    await expect(page.getByRole('timer')).toBeVisible();

    // The counter proves the whole paper was drawn, not one question at a time.
    // Anchored on the counter's own wording: the bare digits regex also
    // matched any answer option that happened to contain numbers.
    await expect(page.getByText(/(Pregunta|Question) 1 (de|of) ([2-5][0-9])\b/)).toBeVisible();
  });

  test('a mock exam is offered for certification tracks and a final exam is not', async ({ page }) => {
    // The two must never be swapped: a certification track has a published
    // blueprint that our invented one would quietly replace.
    const username = uniqueUsername('e2e_kinds_');
    await registerUser(page, { username, displayName: 'E2E Kinds' });

    await page.getByRole('button', { name: 'Rutas' }).click();
    await page.getByRole('tab', { name: /AWS Certified Cloud Practitioner/ }).click();

    await expect(
      page.getByRole('button', { name: /Simulacro de examen|Mock exam/ }),
    ).toBeVisible({ timeout: 15_000 });
    await expect(
      page.getByRole('button', { name: /Examen final del curso|Course final exam/ }),
    ).toHaveCount(0);
  });
});

test.describe('certificate verification', () => {
  test('an unknown code says so instead of leaking whether it exists', async ({ page }) => {
    // Public and unauthenticated on purpose: whoever checks a certificate does
    // not have an account here, so this must work in a fresh context with no
    // session at all.
    await page.goto(`/certificate/${'0'.repeat(32)}`);

    await expect(
      page.getByText(/No encontramos ning.n certificado|could not find a certificate/i),
    ).toBeVisible({ timeout: 15_000 });

    // Nothing on this page may push the visitor into signing up: it is somebody
    // else's proof, not a funnel.
    await expect(page.getByRole('button', { name: /Crear cuenta|Create account/ })).toHaveCount(0);
  });
});
