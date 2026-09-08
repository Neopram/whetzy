const CACHE_NAME = 'whetzy-v2';
const STATIC_ASSETS = ['/', '/index.html', '/manifest.json'];
const OFFLINE_ANSWER_TAG = 'whetzy-sync-answers';

// ── Install: pre-cache static shell ──────────────────────────────────────────
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS)),
  );
  self.skipWaiting();
});

// ── Activate: purge old caches ────────────────────────────────────────────────
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))),
      ),
  );
  self.clients.claim();
});

// ── Fetch: network-first for API, cache-first for assets ─────────────────────
self.addEventListener('fetch', (event) => {
  // Skip non-GET except POST /quiz/answer (handled by background sync)
  if (event.request.method !== 'GET') return;

  const url = new URL(event.request.url);

  if (url.pathname.startsWith('/api/')) {
    // Network-first with cache fallback for GET API calls
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
          return response;
        })
        .catch(() => caches.match(event.request)),
    );
    return;
  }

  // Cache-first for static assets
  event.respondWith(
    caches.match(event.request).then((cached) => {
      const fetchPromise = fetch(event.request).then((response) => {
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        }
        return response;
      });
      return cached || fetchPromise;
    }),
  );
});

// ── Web Push: show notification ───────────────────────────────────────────────
self.addEventListener('push', (event) => {
  if (!event.data) return;
  let payload;
  try {
    payload = event.data.json();
  } catch {
    payload = { title: 'Whetzy', body: event.data.text(), tag: 'whetzy' };
  }
  const { title = 'Whetzy', body = '', tag = 'whetzy', ...rest } = payload;
  event.waitUntil(
    self.registration.showNotification(title, {
      body,
      tag,
      icon: '/icons/icon-192.png',
      badge: '/icons/icon-72.png',
      data: rest,
    }),
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(
    self.clients
      .matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        for (const client of clientList) {
          if ('focus' in client) return client.focus();
        }
        return self.clients.openWindow('/');
      }),
  );
});

// ── Background Sync: flush offline answers ────────────────────────────────────
self.addEventListener('sync', (event) => {
  if (event.tag === OFFLINE_ANSWER_TAG) {
    event.waitUntil(syncPendingAnswers());
  }
});

async function syncPendingAnswers() {
  // The actual flush logic lives in the page via useOfflineSync.
  // Notify all clients to flush their IndexedDB queue.
  const clients = await self.clients.matchAll({ type: 'window' });
  for (const client of clients) {
    client.postMessage({ type: 'SW_SYNC_ANSWERS' });
  }
}
