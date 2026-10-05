# YAM 변경 이력

웹 앱 버전(`web-vX.Y.Z` 태그)과 네이티브 셸 버전(스토어 앱)은 따로 관리한다.
앱은 `server.url` 방식이라 기능 업데이트는 웹 배포(push)만으로 iOS·Android에 반영된다.

## 규칙
- 기능 추가 = MINOR, 버그·문구·데이터 수정 = PATCH
- 릴리스: `index.html`의 `APP_VERSION` 수정 → 이 파일에 항목 추가 → 커밋 → `git tag web-vX.Y.Z` → `git push origin main --tags`
- **데이터(toilets.json 등)를 갱신할 때만** `sw.js`의 `CACHE_NAME`을 올린다. 앱 화면은 Network First라 버전업 때 캐시명을 바꿀 필요가 없고, 바꾸면 사용자 전원이 9MB 데이터를 다시 받는다.
- 네이티브 셸(iOS `MARKETING_VERSION`, Android `versionName`)은 셸을 바꿀 때만 올린다. 다음 셸 배포 때 양쪽 2.0.x로 통일.
- 수정 기준 코드는 이 저장소(yam-toilet) 하나다. `통합 yam/index.html`은 2026-07 보관본이므로 고치지 않는다.

## [web-v2.1.0] - 2026-10-05
### 추가
- 버전 관리 체계 도입: `APP_VERSION` 상수, 이 CHANGELOG, git 태그
- 데이터 출처 화면 하단에 앱 버전 표시

### 수정
- 첫 화면에서 '데이터 출처'를 눌러도 시트가 첫 화면 뒤에 가려 보이지 않던 문제 (overlay·sheet·toast z-index를 landing 위로)

### 이전 기준점
- 이 버전 이전 커밋(`4aeafac`까지)은 태그 없이 배포됨. 셸 버전 현황: iOS 1.0.1(24), Android 2.0.0(14)
