const CACHE_NAME = 'yam-cache-v2'; // 이 숫자를 매번 올릴 필요 없음 — 아래 network-first 전략이 자동으로 최신화함
const urlsToCache = [
  '/',
  '/index.html',
  '/manifest.json'
];

self.addEventListener('install', event => {
  self.skipWaiting(); // 새 SW를 기존 탭 종료 없이 즉시 활성화
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(cacheNames =>
        Promise.all(
          cacheNames
            .filter(name => name !== CACHE_NAME)
            .map(name => caches.delete(name)) // 이전 버전 캐시 자동 삭제
        )
      )
      .then(() => self.clients.claim()) // 이미 열려있는 화면(WebView 포함)에도 즉시 새 SW 적용
  );
});

self.addEventListener('fetch', event => {
  // 카카오맵 API 관련 요청은 항상 네트워크 전용
  if (event.request.url.includes('dapi.kakao.com') || event.request.url.includes('t1.daumcdn.net')) {
    event.respondWith(fetch(event.request));
    return;
  }

  const isAppShell =
    event.request.mode === 'navigate' ||
    event.request.url.endsWith('/index.html') ||
    event.request.url.endsWith('/manifest.json') ||
    new URL(event.request.url).pathname === '/';

  if (isAppShell) {
    // 앱 셸(HTML/manifest)은 Network First — 웹에 새로 올리면 앱(TWA)도 바로 반영됨
    // 네트워크 요청 실패(오프라인) 시에만 캐시된 버전으로 대체
    event.respondWith(
      fetch(event.request)
        .then(response => {
          const cloned = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, cloned));
          return response;
        })
        .catch(() => caches.match(event.request))
    );
    return;
  }

  // 그 외 정적 리소스(toilets.json 등 용량 크고 자주 안 바뀌는 파일)는 Cache First 유지
  event.respondWith(
    caches.match(event.request)
      .then(response => response || fetch(event.request))
  );
});
