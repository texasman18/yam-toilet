#!/usr/bin/env python3
"""간사이 2부 4현 전역 확장. 표준 라이브러리만. merge.py의 정제/30m 중복제거 재사용.
사용: python3 kansai_expand.py   (한 부현이라도 수집 실패 시 japan_toilets.json을 쓰지 않고 종료)
기존 c in osaka/kyoto/kobe/nara 레코드는 버리고 새로 수집한 간사이 전체로 교체, 그 외는 그대로 보존."""
import json, os, shutil, sys, time, urllib.request
import merge  # 같은 폴더의 merge.py: extract_records, dedup_city, strip_internal_fields, validate

URL = "https://overpass-api.de/api/interpreter"
PREFS = [("shiga", "JP-25"), ("kyoto_pref", "JP-26"), ("osaka_pref", "JP-27"),
         ("hyogo", "JP-28"), ("nara_pref", "JP-29"), ("wakayama", "JP-30")]
# 기존 도시 bbox (남,서,북,동) - 순서대로 먼저 맞는 것
BBOXES = [("osaka", (34.57, 135.38, 34.78, 135.61)), ("kyoto", (34.87, 135.55, 35.32, 135.88)),
          ("kobe", (34.62, 135.08, 34.78, 135.32)), ("nara", (34.63, 135.77, 34.72, 135.92))]
OLD_KANSAI = {"osaka", "kyoto", "kobe", "nara"}
OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "japan_toilets.json"))
BACKUP = "/private/tmp/claude-501/-Users-sukjinlee-Documents-Claude----yam/a951503a-8506-42f1-8874-5de7eb0e1526/scratchpad/japan_toilets_before_kansai.json"


def fetch(iso):
    q = (f'[out:json][timeout:300];area["ISO3166-2"="{iso}"]->.a;'
         '(node["amenity"="toilets"](area.a);way["amenity"="toilets"](area.a););out center tags;')
    req = urllib.request.Request(URL, data=q.encode(), method="POST", headers={
        "Content-Type": "text/plain; charset=utf-8",
        "User-Agent": "YAM-toilet-app-data-pipeline/1.0 (contact: internal use)"})
    with urllib.request.urlopen(req, timeout=320) as r:
        return json.loads(r.read().decode())["elements"]


def fetch_retry(iso):
    try:
        return fetch(iso)
    except Exception as e:
        print(f"[ERROR] {iso}: {e} -> 30초 후 재시도", file=sys.stderr)
        time.sleep(30)
        return fetch(iso)  # 두번째 실패는 예외로 전파 -> 파일 안 씀


def city_of(rec, pref):
    for cid, (s, w, n, e) in BBOXES:
        if s <= rec["la"] <= n and w <= rec["ln"] <= e:
            return cid
    return pref


def main():
    raw, seen = {}, set()
    for i, (pid, iso) in enumerate(PREFS):
        els = fetch_retry(iso)
        raw[pid] = els
        print(f"[OK] {pid} ({iso}): {len(els)} elements")
        if i < len(PREFS) - 1:
            time.sleep(5)

    recs, stats = [], {}
    for pid, els in raw.items():
        uniq = []
        for el in els:  # 부현 경계 중복(같은 OSM id) 제거
            k = (el.get("type"), el.get("id"))
            if k not in seen:
                seen.add(k); uniq.append(el)
        r = merge.extract_records(uniq, pid)
        for x in r:
            x["c"] = city_of(x, pid)
        stats[pid] = (len(els), len(r))
        recs.extend(r)
    recs = merge.strip_internal_fields(merge.dedup_city(recs))  # 간사이 전체 1회 (지역 경계 넘는 중복 포함)

    old = json.load(open(OUT, encoding="utf-8"))
    keep = [r for r in old if r["c"] not in OLD_KANSAI]
    final = keep + recs
    merge.validate(final)
    # 기존 비간사이(도쿄-요코하마 295쌍 기존 중복)는 보존 대상이라 간사이 레코드만 검사
    kc = {(r["la"], r["ln"]) for r in keep}
    cs = [(r["la"], r["ln"]) for r in recs]
    assert len(set(cs)) == len(cs) and not (set(cs) & kc), "간사이 완전 동일 좌표 중복"

    if not os.path.exists(BACKUP):
        shutil.copy2(OUT, BACKUP)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, separators=(",", ":"))
    print("부현별(원본,추출):", stats)
    print(f"비간사이 {len(keep)} + 간사이 {len(recs)} = {len(final)}, {os.path.getsize(OUT):,} bytes")


if __name__ == "__main__":
    main()
