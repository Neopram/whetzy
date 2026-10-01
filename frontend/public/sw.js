/* Service worker de Whetzy.
 *
 * La version anterior servia **todo** cache-first, `index.html` incluido, y
 * `CACHE_NAME` era la constante `whetzy-v1`, que nunca cambiaba. Las dos cosas
 * juntas hacen que un despliegue no llegue jamas a quien ya haya visitado el
 * sitio: su `index.html` cacheado sigue apuntando al bundle viejo, y la
 * limpieza del `activate` —que borra las caches cuyo nombre no coincide— no
 * borraba ninguna porque el nombre era siempre el mismo.
 *
 * Paso de verdad: el arreglo que devolvio el backend a la aplicacion estuvo
 * desplegado y el navegador seguia cargando el bundle roto.
 *
 * Reglas ahora:
 *   - la navegacion (el documento HTML) va **network-first**. Es el unico
 *     fichero que no lleva hash en el nombre, asi que es el unico que puede
 *     quedarse obsoleto apuntando a assets que ya no existen. Si no hay red,
 *     se sirve la copia guardada y la aplicacion arranca offline.
 *   - `/assets/*` va cache-first sin caducidad, que es seguro porque Vite les
 *     pone un hash de contenido: si cambia el fichero, cambia la URL.
 *   - la API nunca se cachea de forma que pueda devolver datos de otro dia.
 */

const VERSION = 'v2-2026-09-19';
const CACHE_NAME = `whetzy-${VERSION}`;
const OFFLINE_FALLBACK = '/index.html';

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => cache.addAll([OFFLINE_FALLBACK, '/manifest.json']))
      .catch(() => {})
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((names) =>
        Promise.all(names.filter((n) => n !== CACHE_NAME).map((n) => caches.delete(n)))
      )
      .then(() => self.clients.claim())
  );
});

function esApi(url) {
  return url.pathname.startsWith('/api/') || url.pathname.includes('/api/v1/');
}

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);

  // La API no pasa por aqui: un endpoint servido desde cache devuelve el saldo,
  // la racha o la pregunta de otro momento, que es peor que un error de red.
  if (esApi(url)) return;

  // El documento: red primero, cache solo si no hay red.
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then((res) => {
          // /checkout trae otras cabeceras (sin COEP, CSP de Paddle): no puede
          // ser la copia offline del resto de la app.
          if (url.pathname !== '/checkout') {
            const copia = res.clone();
            caches.open(CACHE_NAME).then((c) => c.put(OFFLINE_FALLBACK, copia)).catch(() => {});
          }
          return res;
        })
        .catch(() => caches.match(OFFLINE_FALLBACK).then((r) => r || Response.error()))
    );
    return;
  }

  // Todo lo demas de nuestro origen: cache primero. Los assets llevan hash, asi
  // que una entrada cacheada nunca queda obsoleta — o esta, o la URL cambio.
  if (url.origin !== self.location.origin) return;

  event.respondWith(
    caches.match(request).then(
      (hit) =>
        hit ||
        fetch(request).then((res) => {
          if (res.ok && res.type === 'basic') {
            const copia = res.clone();
            caches.open(CACHE_NAME).then((c) => c.put(request, copia)).catch(() => {});
          }
          return res;
        })
    )
  );
});
