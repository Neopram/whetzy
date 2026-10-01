import { test, expect } from '@playwright/test';
import { registerUser, markLessonSeen, answerCurrentQuestion, uniqueUsername } from './helpers';

/**
 * 34.3's own criterion: every interactive control reachable at a 390px
 * viewport measures at least 44x44 CSS px (WCAG 2.5.5 / Apple HIG). A CSS
 * fix that only sets `min-width` (no `min-height`) passes a width-only
 * check but still fails real users — that's exactly the bug this spec
 * caught in `.langToggle` (QuizScreen.module.css): width-fixed at 44px,
 * height left at ~18px by the button's own `line-height: normal` and a
 * flex parent with `align-items: center`. Kept as a real, committed spec
 * (not a throwaway `_zzz-*` script) so the audit is reproducible, per the
 * project's own "evidencia ejecutable o no paso" rule.
 */
const VIEWPORT = { width: 390, height: 844 };
const MIN = 44;

type Finding = { where: string; role: string; name: string; width: number; height: number };

async function auditTargets(page: import('@playwright/test').Page, where: string): Promise<Finding[]> {
  return page.evaluate(({ where, min }) => {
    const selectors = 'button, a[href], input, select, textarea, [role="button"]';
    const out: { where: string; role: string; name: string; width: number; height: number }[] = [];
    document.querySelectorAll<HTMLElement>(selectors).forEach((el) => {
      const style = getComputedStyle(el);
      if (style.display === 'none' || style.visibility === 'hidden' || Number(style.opacity) === 0) return;
      const rect = el.getBoundingClientRect();
      if (rect.width === 0 && rect.height === 0) return;

      // WCAG 2.5.5 "Inline" exception: a target whose size is constrained by
      // the line-height of surrounding text (a glossary term inside an
      // explanation sentence) is exempt — GlossaryText.tsx renders exactly
      // that as a <button class="term_...">.
      if (el.className && String(el.className).includes('term_')) return;

      // A checkbox/radio wrapped in its own <label> isn't the real target —
      // the label (AuthScreen.tsx's age-confirmation row) is what receives
      // the click and toggles the input; the input itself stays UA-sized.
      const input = el as HTMLInputElement;
      if ((input.type === 'checkbox' || input.type === 'radio') && el.closest('label')) return;

      if (rect.width < min || rect.height < min) {
        out.push({
          where,
          role: el.tagName.toLowerCase(),
          name: el.getAttribute('aria-label') || el.textContent?.trim().slice(0, 40) || '(sin nombre)',
          width: Math.round(rect.width),
          height: Math.round(rect.height),
        });
      }
    });
    return out;
  }, { where, min: MIN });
}

test.describe('34.3: objetivos tactiles >= 44x44px a 390px', () => {
  test.use({ viewport: VIEWPORT });

  test('Auth, Tracks, Quiz, Lesson', async ({ page }) => {
    const allFindings: Finding[] = [];

    await page.goto('/auth');
    await expect(page.getByRole('button', { name: 'Crear cuenta' })).toBeVisible();
    allFindings.push(...await auditTargets(page, 'Auth — register'));

    await page.getByRole('button', { name: 'Iniciar sesión' }).click();
    await expect(page.getByLabel('Correo electrónico')).toBeVisible();
    allFindings.push(...await auditTargets(page, 'Auth — login'));

    const username = uniqueUsername('e2e_touch_');
    await registerUser(page, { username, displayName: 'Touch Target' });
    await markLessonSeen(page);

    await page.getByRole('button', { name: 'Rutas' }).click();
    await expect(page.locator('[aria-expanded]').first()).toBeVisible({ timeout: 15_000 });
    allFindings.push(...await auditTargets(page, 'Tracks — colapsado'));

    await page.locator('[aria-expanded="false"]').first().click();
    allFindings.push(...await auditTargets(page, 'Tracks — expandido'));

    await page.getByRole('button', { name: /Aprender/ }).first().click();
    const closeLesson = page.getByRole('button', { name: 'Cerrar' });
    await expect(closeLesson).toBeVisible({ timeout: 15_000 });
    allFindings.push(...await auditTargets(page, 'Lesson'));
    await closeLesson.click();

    await page.getByRole('button', { name: 'Hoy', exact: true }).click();
    await page.getByRole('button', { name: 'ESTUDIAR AHORA' }).click();
    await expect(page.locator('[class*="questionCard_"]')).toBeVisible({ timeout: 15_000 });
    allFindings.push(...await auditTargets(page, 'Quiz'));
    await answerCurrentQuestion(page);
    allFindings.push(...await auditTargets(page, 'Quiz — feedback'));

    const summary = allFindings
      .map((f) => `  ${f.where}: <${f.role}> "${f.name}" — ${f.width}x${f.height}px`)
      .join('\n');
    console.log(allFindings.length === 0
      ? 'Sin objetivos por debajo de 44x44px.'
      : `${allFindings.length} objetivo(s) por debajo de 44x44px:\n${summary}`);

    expect(allFindings, summary).toHaveLength(0);
  });
});
