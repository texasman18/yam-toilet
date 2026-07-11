# 트러블슈팅 이력

## 2026-07-11 — 안드로이드(TWA)에서만 "내 위치" 이동 안 됨

### 증상
- Android 비공개 테스트(Alpha) 설치 앱에서 "내 위치" 버튼을 눌러도 지도가 안 옮겨짐
- "위치 권한을 허용해주세요" 배너가 계속 뜸 (Android 시스템 설정에서는 위치 권한 "허용됨" 확인됨)
- 동일 URL을 iOS(Capacitor)와 웹(데스크톱/일반 크롬)에서는 정상 동작
- 설치된 TWA 앱이 아닌, 같은 폰의 일반 Chrome 브라우저로 접속하면 정상 동작 → TWA 전용 문제로 확진

### 원인 (2가지 복합)

**1) `goMyLoc()` 위치 요청 타임아웃/에러 처리 미흡 (index.html)**
- `enableHighAccuracy:true` + `timeout:8000`(8초)로만 요청 → 실내/도심(강남역 등 건물 밀집 지역)에서 GPS 정밀 측위가 8초를 넘기는 경우가 흔함
- 에러 콜백이 에러 종류(권한거부/시간초과/신호없음)를 구분하지 않고 전부 "권한 허용" 메시지로 표시
- `myLat/myLng` 기본값이 강남역 좌표(37.4979, 127.0276)로 하드코딩되어 있어, 실패 시 이 좌표로 조용히 폴백됨

**2) `assetlinks.json`(Digital Asset Links) 미배포**
- `twa-manifest.json`에 `fallbackType: "customtabs"`, `fingerprints: []`로 되어 있었고, 실제로 `https://texasman18-yam-toilet-rhgz.vercel.app/.well-known/assetlinks.json`이 404였음
- TWA가 정식 신뢰관계(verified) 없이 격리된 Custom Tabs 세션으로 동작 → Android 앱 단위 위치 권한이 Chrome의 사이트 단위 위치 권한으로 위임(delegate)되지 않음
- 이 격리된 세션은 평소 쓰는 크롬의 위치 캐시도 공유받지 못해 콜드 스타트로 매번 새로 측위해야 함

### 해결

**코드 수정** (`index.html`, 커밋 `f53e437`)
- 1차 시도: `enableHighAccuracy:true, timeout:15000`
- 실패 시(PERMISSION_DENIED 제외) 2차 시도: `enableHighAccuracy:false, timeout:10000` (Wi-Fi/기지국 기반 저정밀 재시도)
- 에러 코드 1(권한거부)일 때만 "위치 권한을 허용해주세요", 그 외는 "GPS 신호가 약해요. 잠시 후 다시 시도해주세요"(`toastLocWeak`, KO/EN)로 메시지 분리

**assetlinks.json 배포** (커밋 `81115dd`)
- Play Console → Google Play로 보호됨 → Play 스토어 보호 → Play 앱 서명 관리 에서 **App Signing Key SHA-256 지문** 확인
  (Play 앱 서명 사용 중이므로 로컬 업로드 키스토어 지문이 아니라 이 값을 써야 함)
- `.well-known/assetlinks.json` 생성 후 배포:
  ```json
  [{
    "relation": ["delegate_permission/common.handle_all_urls"],
    "target": {
      "namespace": "android_app",
      "package_name": "kr.techcel.yam2",
      "sha256_cert_fingerprints": [
        "65:EF:45:6E:64:41:20:B9:BF:2D:48:39:34:44:F1:E4:A6:FD:4E:5A:3F:95:18:7F:B9:93:89:84:A8:03:12:DF"
      ]
    }
  }]
  ```
- Google 공식 검증 API(`digitalassetlinks.googleapis.com/v1/statements:list`)로 정상 검증 확인
- Android가 검증 결과를 캐시하므로, 테스트 기기에서 **앱 완전 삭제 후 재설치**해야 재검증되어 반영됨

### 참고
- 앱 셸(`index.html`)은 `sw.js`에서 Network First 캐싱이라, 이런 JS/HTML 수정은 **네이티브 빌드(Play Console 제출) 없이도** 앱 재실행만으로 반영됨. assetlinks.json 같은 네이티브 신뢰관계 이슈만 앱 재설치가 필요.
- `/Users/sukjinlee/Library/Mobile Documents/.../Documents/Claude/YAM/assetlinks.json` (yam-toilet 밖, 루트) 에 구버전 패키지명(`kr.techcel.yam`) 기준의 오래된 assetlinks.json이 남아있음 — 실제 배포 경로가 아니라 미사용 상태지만 혼동 방지 위해 추후 정리 권장.
