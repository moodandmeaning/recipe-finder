// Offline support: the app shell is cached, recipes.json is network-first, photos are cached as they load.
const SHELL = 'shell-v1';
const IMAGES = 'images-v1';
const MAX_IMAGES = 300;
const SHELL_FILES = [
  './', 'index.html', 'css/style.css', 'js/app.js', 'js/i18n.js',
  'manifest.webmanifest', 'icons/icon-192.png', 'icons/icon-512.png',
];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(SHELL).then((c) => c.addAll(SHELL_FILES)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys()
    .then((keys) => Promise.all(keys.filter((k) => k !== SHELL && k !== IMAGES).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});

async function networkFirst(req) {
  const cache = await caches.open(SHELL);
  try {
    const res = await fetch(req);
    if (res.ok) cache.put(req, res.clone());
    return res;
  } catch {
    return (await cache.match(req, { ignoreSearch: true })) || Response.error();
  }
}

async function image(req) {
  const cache = await caches.open(IMAGES);
  const hit = await cache.match(req);
  if (hit) return hit;
  const res = await fetch(req);
  if (res.ok || res.type === 'opaque') {
    await cache.put(req, res.clone());
    const keys = await cache.keys();
    if (keys.length > MAX_IMAGES) await Promise.all(keys.slice(0, keys.length - MAX_IMAGES).map((k) => cache.delete(k)));
  }
  return res;
}

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (req.destination === 'image' && url.origin !== location.origin) {
    e.respondWith(image(req));
  } else if (url.origin === location.origin) {
    // Network-first everywhere on our own origin, so updates show up right away when online.
    e.respondWith(networkFirst(req));
  }
});
