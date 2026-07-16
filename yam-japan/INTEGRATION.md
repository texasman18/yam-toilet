# YAM 본 앱 통합 명세 (yam-japan → YAM/index.html JP 모드)

본 문서는 yam-japan 독립 웹앱을 나중에 본 앱(KR/JP 국가 모드)에 합칠 때 이식할 목록이다.
상위 설계: `기획/일본햘 기획서들/YAM_일본확장_기술설계서_v1.md` (2축 상태 모델 curCountry×curLang, §2~§6).
3개국 통합 시에는 `기획/통합 기획서들/YAM_3개국통합_기술설계서_v1.md`가 우선.

## 1. 그대로 이식할 코드 블록 (yam-japan/index.html 기준)

| 블록 | 내용 | 비고 |
|---|---|---|
| `LANG.jp` | JP 모드 한국어 UI 문구 (toastNoCity·landCityLabel 포함) | 본 앱 LANG에 jp 키로 추가 |
| `JP_CITIES` + `cityOf()` | 10개 도시 테이블 (도쿄=도쿄도 본토 전역, 오사카시·교토시 전역 bbox) | GPS 도시 판정 |
| `DEFAULT_VIEW` | 기본 화면 = 신주쿠역 35.6896,139.7006 줌 15, `fallbackDefault()` | GPS 실패/일본 밖 폴백 |
| `JA_KO`+`KANA_BASE`+`KANA_DI`+`addCoda()`+`kanaToKo()`+`translateToKo()` | **일본어→한글 표시 변환** (사전 ~170개: 시설용어+10개 도시 지명, 가나 음차: 촉음=ㅅ받침·발음=ㄴ받침·장음 생략, 미등록 한자 원문 유지) | KO_EN/translateToEn과 같은 패턴. JP 모드에서만 호출 |
| `EXCLUDE_JP`/`VALID_JP`/`isInvalidJP()` | Google Places 결과 필터 | |
| `loadJapanData()` | lazy-load, **경로 자동 감지**(`location.pathname`이 /yam-japan이면 그 하위), 실패 시 재시도(실패를 캐시하지 않음) | 본 앱 통합 시 base='' 케이스 |
| `addJapanBundle()`/`addGooglePlacesJP()`/`finishSearch()` | 검색 파이프: 번들(반경 800m)+Places(公衆トイレ/トイレ, language:ko), isDup 30m | searchNear에 curCountry==='jp' 분기로 삽입 |
| JP 상세 시트 | 한글 이름(translateToKo) + `.det-jp` 일본어 원문 병기 + 설비 뱃지(♿🚼⚕️ r.f) + 버튼 3종(구글맵 길찾기/Apple 지도/주소 복사 — 주소 없으면 복사 숨김, 카카오·네이버 없음) | openDetail JP 분기 |
| `doSearch` JP 분기 | `google.maps.Geocoder().geocode({address,region:'JP',language:'ko'})` | Kakao는 일본 지명 불가 |
| `updateLoc` JP 분기 | Geocoder language:'ko' + **일본 세부지명은 한국어 미지원(로마자)** → cityOf 매칭 시 한국어 도시명 접두 표기 | |
| 지도 옵션 | `gestureHandling:'greedy'`, `clickableIcons:false` | JP 모드 Google 지도 생성 시 |
| 출처(ⓘ) 시트 | ODbL 고지 + Google 포함 문구 + 지자체(CC BY) 추가 예정 | openSourceSheet |

## 2. UX 결정 사항 (2026-07-16 사용자 확정)

- 지도 화면에 도시 칩 **없음** — 제공 도시는 랜딩에 필(pill)로만 표출("현재 제공되는 도시입니다")
- 기본 화면 = 신주쿠. GPS 성공 & 일본 내 → 현재 위치 자동 이동 (10개 도시 밖이어도 일본이면 GPS 위치에서 검색)
- 제공 도시 밖 GPS → 토스트 "현재 도시는 화장실 찾기가 제공되지 않습니다" (자동 소멸), 일본 밖이면 신주쿠 폴백
- 화장실 이름은 **한글 표시**가 기본, 상세 시트에 일본어 원문 병기(현지인 제시용). 주소는 원문 유지

## 3. 데이터·배포

- `japan_toilets.json` 8,835건/1.04MB — OSM 전용(ODbL), 스키마 `{n,a,la,ln,t,h,p,c,s,f}`. 지자체 오픈데이터(CC BY) 병합은 후속 (`s:"city"` 예약)
- 파이프라인: `pipeline/fetch_osm.py`(Overpass, 도시별 재수집은 raw 파일 삭제 후 재실행) → `merge.py`(30m 격자 중복제거+검증)
- 배포 2곳: ① 독립 저장소 `texasman18/Yam-Japan` → yam-japan.vercel.app (현행 서비스) ② 본 저장소 yam-japan/ 하위폴더 (vercel.json에 /yam-japan rewrite 이미 추가됨)
- Google Maps 키 리퍼러: yam-japan.vercel.app/* 등록 완료 (2026-07-16)
- 본 앱 통합 시 sw.js 캐시 목록에 japan_toilets.json **넣지 말 것** (lazy-load 취지)

## 4. 통합 순서 (기술설계서 §7 승계)

P1 동작불변 리팩터(isGoogleMap 치환·Google 동적 로더) → P2 JP 모드 이식(위 1장 블록) → P3 GPS 자동 국가 전환(countryOf, 수동 우선 매너 규칙은 3개국 통합설계서 참조). 커밋 분리 필수, KR 모드 회귀 0 확인.
