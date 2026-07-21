// Minimal, deliberately conservative service worker.
//
// Its only job is to make the app installable (Add to Home Screen ->
// fullscreen launch on a tablet) and to speed up repeat loads by caching the
// content-hashed build assets, which are immutable so they can never go stale.
//
// It intentionally does NOT cache API responses or page navigations, so your
// data is always fresh and there is no risk of serving stale content.

const ASSET_CACHE = "study-agent-assets-v1";

self.addEventListener("install", (event) => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(keys.filter((k) => k !== ASSET_CACHE).map((k) => caches.delete(k)))
      )
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // Cache-first only for our own hashed build assets. Everything else -
  // API calls, navigations, external requests - passes straight through.
  const isImmutableAsset =
    url.origin === self.location.origin && url.pathname.startsWith("/assets/");

  if (event.request.method === "GET" && isImmutableAsset) {
    event.respondWith(
      caches.open(ASSET_CACHE).then(async (cache) => {
        const hit = await cache.match(event.request);
        if (hit) return hit;
        const resp = await fetch(event.request);
        if (resp.ok) cache.put(event.request, resp.clone());
        return resp;
      })
    );
  }
  // else: default network handling (no respondWith).
});
