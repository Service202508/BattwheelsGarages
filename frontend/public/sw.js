// Battwheels OS Service Worker
// IMPORTANT: HTML documents are NEVER cached — only immutable static assets.
// This prevents the SPA shell (index.html) from being served stale for all routes.

const CACHE_NAME = 'battwheels-v2';

// Only cache truly immutable assets — NOT the HTML document ('/')
const STATIC_ASSETS = [
  '/manifest.json',
  '/icon-192.png',
  '/icon-512.png',
];

// Install: cache only static assets (no HTML)
self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
  );
});

// Activate: clean up old caches (including the old v1 cache that cached '/')
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

// Fetch: always network-first for HTML navigation and API calls
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET and non-HTTP(S) requests
  if (request.method !== 'GET' || !url.protocol.startsWith('http')) return;

  // API calls: network-only, no caching
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request).catch(() => new Response(JSON.stringify({ error: 'offline' }), {
        status: 503,
        headers: { 'Content-Type': 'application/json' }
      }))
    );
    return;
  }

  // HTML navigation requests (page loads): ALWAYS go to network
  // This prevents stale HTML shells being served for SPA routes like /dashboard
  if (request.mode === 'navigate') {
    event.respondWith(fetch(request));
    return;
  }

  // Static assets (JS/CSS chunks, images): cache-first with network fallback
  // No HTML fallback — a missing asset should fail loudly, not return a cached page
  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) return cached;
      return fetch(request).then((response) => {
        if (response.ok && response.type !== 'opaque') {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
        }
        return response;
      });
    })
  );
});
