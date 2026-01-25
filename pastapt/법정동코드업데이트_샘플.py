import os
import csv
import sqlite3
from typing import Dict, List, Optional, Tuple

# ===== 경로 설정 =====
# PAST_APT_BASE_PATH는 프로젝트에서 이미 정의되어 있다고 가정
PAST_APT_BASE_PATH = os.getenv("PAST_APT_BASE_PATH", ".")
DB_FILENAME = os.path.join(PAST_APT_BASE_PATH, "past_apt_data.db")
PAST_APT_TABLE = "past_apt"

# apt 폴더에 있는 법정동코드.txt (탭 구분, 헤더 포함)
LEGAL_CODE_TXT = os.path.join(PAST_APT_BASE_PATH, "../apt", "법정동코드.txt")


# ---------------------------------------------
# ② 법정동코드 로딩/인덱싱 (폐지여부=존재만)
# ---------------------------------------------
def load_active_legal_codes(txt_path: str) -> List[Tuple[str, str]]:
    """
    법정동코드.txt를 읽어 ('법정동코드', '법정동명') 튜플 리스트로 반환.
    폐지여부 == '존재'만 포함.
    """
    rows: List[Tuple[str, str]] = []
    with open(txt_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        # 파일 헤더 예시: 법정동코드, 법정동명, 폐지여부
        for r in reader:
            if (r.get("폐지여부") or "").strip() == "존재":
                code = (r.get("법정동코드") or "").strip()
                name = (r.get("법정동명") or "").strip()
                if code and name:
                    rows.append((code, name))
    return rows


def build_name_indexes(active_codes: List[Tuple[str, str]]):
    """
    빠른 조회를 위한 보조 인덱스 구성.
    - full_name_to_code: 법정동명(full) → 코드
    - endswith_map: '마지막 두 토큰' 문자열 → 해당 전체이름 목록(중복/모호성 처리용)
      예) '청주시 서원구', '서울특별시 중구', '중구 동자동' 등
    """
    full_name_to_code: Dict[str, str] = {}
    endswith_map: Dict[str, List[str]] = {}

    for code, full_name in active_codes:
        full_name_to_code[full_name] = code

        parts = full_name.split()
        if len(parts) >= 2:
            key2 = " ".join(parts[-2:])  # 마지막 두 토큰
            endswith_map.setdefault(key2, []).append(full_name)

        # 동(읍/면/가) 단위까지 있는 경우 3토큰 키도 추가 (모호성 감소)
        if len(parts) >= 3:
            key3 = " ".join(parts[-3:])
            endswith_map.setdefault(key3, []).append(full_name)

    return full_name_to_code, endswith_map


def find_legal_code(
    region_name: str,
    mcode_name: str,
    full_name_to_code: Dict[str, str],
    endswith_map: Dict[str, List[str]],
) -> Optional[Tuple[str, str]]:
    """
    region_name, mcode_name으로 법정동코드를 탐색.
    반환: (code, matched_full_name) 또는 None

    우선순위:
    1) 정확히 'region_name mcode_name' 전체이름과 일치
    2) '... region_name mcode_name' 으로 끝나는 전체이름(유일)
    3) '... mcode_name' 으로 끝나고, 이름 어딘가에 region_name이 포함(유일)
    """
    rn = (region_name or "").strip()
    mn = (mcode_name or "").strip()
    if not rn or not mn:
        return None

    target_full = f"{rn} {mn}"

    # 1) 완전일치
    if target_full in full_name_to_code:
        return full_name_to_code[target_full], target_full

    # 2) 끝단 2~3토큰 키로 좁혀서 유일매칭 시도
    candidates: List[str] = []
    # 마지막 두 토큰 키
    if target_full in endswith_map:
        candidates.extend(endswith_map[target_full])

    # ‘시/도 포함 전체 이름 … rn mn’으로 끝나는 것들 추가 스캔 (안전망)
    if not candidates:
        # endswith_map을 전수검사하지 않고, 키 후보를 생성해 조회
        # 예: rn='청주시', mn='서원구' → key='청주시 서원구'
        key2 = f"{rn} {mn}"
        if key2 in endswith_map:
            candidates.extend(endswith_map[key2])

    # 2-보강) 그래도 없으면 endswith 스캔(성능보단 정확성 우선)
    if not candidates:
        # endswith_map의 키들을 역참조하는 대신 전체 이름을 한 번 스캔
        # 성능이 걱정되면 별도 suffix 인덱스를 확장하세요.
        for full in full_name_to_code.keys():
            if full.endswith(f"{rn} {mn}"):
                candidates.append(full)

    # 유일하면 확정
    if len(set(candidates)) == 1:
        full = candidates[0]
        return full_name_to_code[full], full

    # 3) mcode_name만 끝단 매칭 + region_name 포함(유일)
    candidates2: List[str] = []
    for full in full_name_to_code.keys():
        if full.endswith(mn) and rn in full:
            candidates2.append(full)

    if len(set(candidates2)) == 1:
        full = candidates2[0]
        return full_name_to_code[full], full

    # 모호하거나 없음
    return None


# ---------------------------------------------
# ① DB 스캔하여 stdg_cd 업데이트
# ---------------------------------------------
def update_stdg_cd_with_legal_codes(db_path: str, code_txt_path: str, batch_size: int = 500):
    # 2) 코드 로딩 & 인덱싱 (사용자 제안대로 먼저)
    active = load_active_legal_codes(code_txt_path)
    #
    full_name_to_code, endswith_map = build_name_indexes(active)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # 성능을 위해 보조 인덱스 권장
    # cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{PAST_APT_TABLE}_region_mcode ON {PAST_APT_TABLE}(region_name, mcode_name)")
    # cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{PAST_APT_TABLE}_stdg_cd ON {PAST_APT_TABLE}(stdg_cd)")

    # stdg_cd가 비었거나 자리수 미달(관례상 10자리)인 경우만 타깃
    cur.execute(f"""
        SELECT id, region_name, mcode_name, COALESCE(stdg_cd, '')
        FROM {PAST_APT_TABLE}
        WHERE stdg_cd IS NULL
           OR TRIM(stdg_cd) = ''
           OR LENGTH(TRIM(stdg_cd)) < 10
    """)

    rows = cur.fetchall()

    updates: List[Tuple[str, int]] = []
    unresolved: List[Tuple[int, str, str]] = []

    for (rid, region_name, mcode_name, _stdg) in rows:
        found = find_legal_code(region_name, mcode_name, full_name_to_code, endswith_map)
        # print(rid, region_name, mcode_name, "→", found)
        if found:
            print(rid, region_name, mcode_name, "→", found)
            stdg_cd, matched_name = found
            updates.append((stdg_cd, rid))
        else:
            # 미해결 케이스 기록
            unresolved.append((rid, region_name or "", mcode_name or ""))

        # 배치 업데이트
        if len(updates) >= batch_size:
            cur.executemany(f"UPDATE {PAST_APT_TABLE} SET stdg_cd=? WHERE id=?", updates)
            conn.commit()
            updates.clear()

    # 남은 배치 커밋
    if updates:
        cur.executemany(f"UPDATE {PAST_APT_TABLE} SET stdg_cd=? WHERE id=?", updates)
        conn.commit()

    print("=== 결과 요약 ===")
    print(f"총 대상 행: {len(rows)}")
    print(f"성공 업데이트: {len(rows) - len(unresolved)}")
    print(f"미해결: {len(unresolved)}")

    if unresolved:
        # 필요 시 파일로 떨굴 수 있음
        print("\n미해결 샘플 상위 20건:")
        for rid, rn, mn in unresolved[:20]:
            print(f" - id={rid}, region='{rn}', mcode='{mn}'")

    conn.close()


# --------------------
# 실행 예시
# --------------------
if __name__ == "__main__":
    if not os.path.exists(DB_FILENAME):
        raise FileNotFoundError(f"DB not found: {DB_FILENAME}")
    if not os.path.exists(LEGAL_CODE_TXT):
        raise FileNotFoundError(f"법정동 코드 파일 없음: {LEGAL_CODE_TXT}")

    update_stdg_cd_with_legal_codes(DB_FILENAME, LEGAL_CODE_TXT)
