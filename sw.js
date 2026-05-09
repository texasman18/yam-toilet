const CACHE_NAME = 'yam-cache-v1';
const urlsToCache = [
  '/',
  '/index.html',
  '/manifest.json'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  // 카카오맵 API 관련 요청은 네트워크를 우선하거나 네트워크 전용으로 처리
  if (event.request.url.includes('dapi.kakao.com') || event.request.url.includes('t1.daumcdn.net')) {
    event.respondWith(fetch(event.request));
    return;
  }

  // 나머지 정적 리소스는 Cache First 전략
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // 캐시에 있으면 반환
        if (response) {
          return response;
        }
        // 없으면 네트워크 요청
        return fetch(event.request);
      })
  );
});
