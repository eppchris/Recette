// Service Worker — Recette PWA v5
const SHELL_CACHE = 'recette-shell-v5';
const API_CACHE   = 'recette-api-v5';

const SHELL_ASSETS = [
  '/mobile/fr',
  '/mobile/jp',
  '/static/favicon-64x64.png',
  '/static/mobile/manifest-fr.json',
  '/static/mobile/manifest-jp.json',
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(SHELL_CACHE)
      .then(cache => cache.addAll(SHELL_ASSETS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys
          .filter(k => k !== SHELL_CACHE && k !== API_CACHE)
          .map(k => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  if (request.method !== 'GET') return;
  if (url.origin !== self.location.origin) return;

  if (url.pathname.startsWith('/api/mobile/')) {
    event.respondWith(networkFirstThenCache(request, API_CACHE));
  } else if (url.pathname.startsWith('/mobile/')) {
    event.respondWith(networkFirstThenCache(request, SHELL_CACHE));
  } else if (url.pathname.startsWith('/static/')) {
    event.respondWith(cacheFirst(request, SHELL_CACHE));
  }
});

async function networkFirstThenCache(request, cacheName) {
  const cache = await caches.open(cacheName);
  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) cache.put(request, networkResponse.clone());
    return networkResponse;
  } catch (e) {
    const cached = await cache.match(request);
    if (cached) return cached;
    return new Response(JSON.stringify({ error: 'Hors ligne' }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}

async function cacheFirst(request, cacheName) {
  const cache  = await caches.open(cacheName);
  const cached = await cache.match(request);
  if (cached) return cached;
  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) cache.put(request, networkResponse.clone());
    return networkResponse;
  } catch (e) {
    return new Response('Hors ligne', { status: 503 });
  }
}
