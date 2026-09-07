export type Theme = 'light' | 'dark';

const THEME_KEY = 'whetzy_theme';

export function getStoredTheme(): Theme {
  try {
    const v = localStorage.getItem(THEME_KEY);
    if (v === 'light' || v === 'dark') return v;
  } catch {
    /* storage unavailable */
  }
  // Whetzy ships in LIGHT mode by default.
  return 'light';
}

export function applyTheme(theme: Theme) {
  document.documentElement.setAttribute('data-theme', theme);
  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) meta.setAttribute('content', theme === 'dark' ? '#1A1A2E' : '#1CB0F6');
  try {
    localStorage.setItem(THEME_KEY, theme);
  } catch {
    /* ignore */
  }
}

export function initTheme() {
  applyTheme(getStoredTheme());
}

export function toggleTheme(): Theme {
  const next: Theme = getStoredTheme() === 'light' ? 'dark' : 'light';
  applyTheme(next);
  return next;
}
