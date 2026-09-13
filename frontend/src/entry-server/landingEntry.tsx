/**
 * Build-time-only entry point for prerendering the marketing landing (11.11).
 *
 * NOT part of the client bundle: src/main.tsx never imports this file, so it
 * is unreachable from index.html's module graph and Vite's normal `vite
 * build` never includes it. It exists solely for scripts/prerender-landing.mjs,
 * which compiles it with Vite's own `--ssr` build (so the `LandingScreen.css`
 * import is handled the same way Vite always handles CSS-in-SSR — stubbed out,
 * since no styles need to be inlined into the HTML response) and then runs
 * the compiled output in plain Node to render the real component to static
 * markup. This keeps the hero copy in exactly one place: LandingScreen.tsx.
 *
 * Renders the Spanish (default) copy — see the i18n import below and
 * scripts/prerender-landing.mjs for why, and for the `?lang=en` trade-off.
 */
import { renderToStaticMarkup } from 'react-dom/server';

// Side-effecting import: registers the global i18next instance that
// react-i18next's useTranslation() reads from when there is no
// <I18nextProvider> in the tree (same pattern src/main.tsx relies on).
// Its `lng: 'es'` default is what makes this a Spanish prerender.
import '../i18n';

import { LandingScreen } from '../pages/LandingScreen';

export function renderLandingHtml(): string {
  return renderToStaticMarkup(<LandingScreen />);
}
