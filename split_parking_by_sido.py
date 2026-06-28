"""
전국주차장정보표준데이터.json 을 시도별로 분리하여
data/parking/{시도명}.json 으로 저장
"""

import json
import os
from collections import defaultdict

SRC = os.path.join(os.path.dirname(__file__), "manual", "전국주차장정보표준데이터.json")
OUT_DIR = os.path.join(os.path.dirname(__file__), "data", "parking")


def extract_sido(record: dict) -> str:
    """주소(도로명 우선, 없으면 지번)에서 시도명 추출"""
    addr = record.get("소재지도로명주소") or record.get("소재지지번주소") or ""
    addr = addr.strip()
    if not addr:
        return "기타"
    return addr.split()[0]


def main():
    print(f"읽는 중: {SRC}")
    with open(SRC, encoding="utf-8") as f:
        data = json.load(f)

    records = data["records"]
    fields = data["fields"]
    print(f"총 레코드 수: {len(records):,}")

    # 시도별로 분류
    sido_map: dict[str, list] = defaultdict(list)
    for rec in records:
        sido = extract_sido(rec)
        sido_map[sido].append(rec)

    # 시도 목록 출력
    print("\n시도별 건수:")
    for sido, recs in sorted(sido_map.items()):
        print(f"  {sido}: {len(recs):,}건")

    # 출력 폴더 생성
    os.makedirs(OUT_DIR, exist_ok=True)

    # 시도별 파일 저장
    for sido, recs in sido_map.items():
        out = {"fields": fields, "records": recs}
        path = os.path.join(OUT_DIR, f"{sido}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
        print(f"저장 완료: {sido}.json ({len(recs):,}건)")

    print(f"\n완료: {len(sido_map)}개 파일 → {OUT_DIR}")


if __name__ == "__main__":
    main()
