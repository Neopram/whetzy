// @vitest-environment node
//
// Regression for the landing prerender silently shipping in English (30.4).
// This file runs with NO `window` — the same shape as
// scripts/prerender-landing.mjs's plain-Node execution, unlike every other
// test file here (jsdom, which has `window`). Node 21+ ships its own global
// `navigator` with a real `.language` derived from the OS/ICU locale, so a
// check keyed on `typeof navigator === 'undefined'` silently breaks the
// moment the Node version running the build has that global — verified live
// on Node 22 (`navigator.language` resolves to "en-US" here), while
// `.nvmrc` pins 20.19.0, which has no such global. `typeof window` has no
// such version dependency: Node never defines it, in any version.
import { describe, expect, it } from 'vitest';

describe('i18n default language outside a browser (SSR / prerender)', () => {
  it('is always Spanish, even when the Node runtime has a global navigator', async () => {
    expect(typeof window).toBe('undefined');
    const i18n = (await import('../i18n')).default;
    expect(i18n.language).toBe('es');
  });
});
