const CACHE_NAME = 'dav-ai-app-shell-v1'
const APP_SHELL_URLS = ['/', '/manifest.webmanifest', '/favicon.svg', '/pwa-icon.svg']
const CACHEABLE_DESTINATIONS = new Set(['script', 'style', 'image', 'font', 'manifest'])

function isSameOriginAppRequest(request) {
  const url = new URL(request.url)
  return request.method === 'GET' && url.origin === self.location.origin
}

function isApiRequest(request) {
  const url = new URL(request.url)
  return url.pathname.startsWith('/api/')
}

function isCacheableStaticRequest(request) {
  const url = new URL(request.url)
  return (
    CACHEABLE_DESTINATIONS.has(request.destination) ||
    url.pathname.startsWith('/assets/') ||
    APP_SHELL_URLS.includes(url.pathname)
  )
}

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => cache.addAll(APP_SHELL_URLS))
      .then(() => self.skipWaiting()),
  )
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((cacheNames) =>
        Promise.all(
          cacheNames
            .filter((cacheName) => cacheName !== CACHE_NAME)
            .map((cacheName) => caches.delete(cacheName)),
        ),
      )
      .then(() => self.clients.claim()),
  )
})

self.addEventListener('fetch', (event) => {
  const { request } = event

  if (!isSameOriginAppRequest(request) || isApiRequest(request)) {
    return
  }

  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const responseToCache = response.clone()
          caches.open(CACHE_NAME).then((cache) => cache.put('/', responseToCache))
          return response
        })
        .catch(() => caches.match('/')),
    )
    return
  }

  if (!isCacheableStaticRequest(request)) {
    return
  }

  event.respondWith(
    caches.match(request).then((cachedResponse) => {
      if (cachedResponse) {
        return cachedResponse
      }

      return fetch(request).then((response) => {
        const responseToCache = response.clone()
        caches.open(CACHE_NAME).then((cache) => cache.put(request, responseToCache))
        return response
      })
    }),
  )
})
