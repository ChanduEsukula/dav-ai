// Retire the legacy app-shell service worker and its cache after the scope change.
self.addEventListener('install', () => self.skipWaiting())
self.addEventListener('activate', event => {
  event.waitUntil(Promise.all([
    caches.keys().then(keys => Promise.all(keys.filter(key => key.startsWith('dav-ai-app-shell-')).map(key => caches.delete(key)))),
    self.registration.unregister(),
  ]).then(() => self.clients.claim()))
})
