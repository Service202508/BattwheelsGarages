// Battwheels OS Service Worker
const CACHE_NAME = 'battwheels-os-v1';

// Assets to cache on install (shell caching)
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
];

// Install: cache static assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

// Activate: clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// Fetch: Network first, fall back to cache for navigation requests
// API calls always go to network (never cache)
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Never cache API calls
  if (url.pathname.startsWith('/api/')) return;

  // For navigation (HTML pages): network first, fallback to cached index.html
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request).catch(() => caches.match('/index.html'))
    );
    return;
  }

  // For static assets: cache first
  event.respondWith(
    caches.match(request).then((cached) => cached || fetch(request))
  );
});
