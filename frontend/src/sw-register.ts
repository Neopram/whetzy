export function registerServiceWorker() {
  // Only register the SW in production builds — in dev it aggressively caches
  // the bundle and serves stale modules across reloads/HMR.
  if (import.meta.env.PROD && 'serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/sw.js').catch(() => {});
    });
  }
}
