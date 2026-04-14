# 법정동코드 생성 및 변환 유틸리티
# -*- coding: utf-8 -*-
import os
import sqlite3
import csv
import re
from typing import Optional, Dict, List

from config import PUBLIC_BASE_PATH

DB_PATH = os.path.join(PUBLIC_BASE_PATH, "public_data.db")
TABLE_NAME = "lawd_code"

# ==========================
# 공용: DB 커넥션
# ==========================
def get_conn(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

# ==========================
# 1) 테이블 생성
# ==========================
def init_lawd_db(db_path: str = DB_PATH) -> None:
    """
    lawd_code(lawd_cd TEXT, lawd_name TEXT)
    - lawd_cd를 PRIMARY KEY로 설정(= 인덱스 포함)
    """
    ddl = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        lawd_cd   TEXT PRIMARY KEY,
        lawd_name TEXT NOT NULL,
        batch_apt_yn  TEXT DEFAULT 'N',  -- 국토부 실거래처리(아파트,빌라,상가) 배치처리 여부 (Y/N
        batch_villa_yn  TEXT DEFAULT 'N',
        batch_sanga_yn  TEXT DEFAULT 'N' 
    );
    """
    conn = get_conn(db_path)
    try:
        conn.execute(ddl)
        conn.commit()
    finally:
        conn.close()

# ==========================
# 2) TXT 읽어서 로드(‘존재’만)
# ==========================
def load_lawd_from_txt(txt_path: str, db_path: str = DB_PATH) -> int:
    """
    탭 구분 텍스트(헤더 포함)를 읽어 ‘폐지여부’가 ‘존재’인 행만 INSERT OR REPLACE.
    컬럼: 법정동코드, 법정동명, 폐지여부
    반환: 적재한(INSERT/REPLACE) 행 수
    """
    init_lawd_db(db_path)

    if not os.path.exists(txt_path):
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {txt_path}")

    # UTF-8 BOM 유연 처리
    inserted = 0
    conn = get_conn(db_path)
    try:
        sql = f"INSERT OR REPLACE INTO {TABLE_NAME} (lawd_cd, lawd_name) VALUES (?, ?)"
        with open(txt_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f, delimiter="\t")
            header = next(reader, None)

            # 헤더 유효성(유연 매칭)
            if header is None or len(header) < 3:
                raise ValueError("입력 파일의 헤더가 유효하지 않습니다. (법정동코드, 법정동명, 폐지여부)")

            # 컬럼 인덱스 탐색(한글 헤더 그대로일 때)
            try:
                idx_code = header.index("법정동코드")
                idx_name = header.index("법정동명")
                idx_stat = header.index("폐지여부")
            except ValueError:
                # 예상 헤더명이 아닐 경우, 위치 기반으로도 허용(1,2,3열)
                idx_code, idx_name, idx_stat = 0, 1, 2

            rows = []
            for row in reader:
                if not row or len(row) <= max(idx_code, idx_name, idx_stat):
                    continue
                code = row[idx_code].strip()
                name = row[idx_name].strip()
                stat = row[idx_stat].strip()

                # ‘존재’만 반영
                if stat == "존재" and code and name:
                    rows.append((code, name))

            if rows:
                conn.executemany(sql, rows)
                conn.commit()
                inserted = len(rows)
    finally:
        conn.close()

    return inserted

# ==========================
# 3) lawd_cd로 단건 조회
# ==========================
def get_lawd_by_code(lawd_cd: str, db_path: str = DB_PATH) -> Optional[Dict[str, str]]:
    """
    lawd_cd로 lawd_code 테이블에서 단건 조회.
    반환: {"lawd_cd": "...", "lawd_name": "..."} 또는 None
    """
    if not lawd_cd:
        return None

    conn = get_conn(db_path)
    try:
        sql = f"SELECT lawd_cd, lawd_name FROM {TABLE_NAME} WHERE lawd_cd = ?"
        cur = conn.execute(sql, (str(lawd_cd),))
        row = cur.fetchone()
        if not row:
            return None
        return {"lawd_cd": row[0], "lawd_name": row[1]}
    finally:
        conn.close()

# ==========================
# 3) lawd_name로 단건 조회
# ==========================
def get_lawd_by_name(address: str, db_path: str = DB_PATH) -> Optional[Dict[str, str]]:
    """
    주소를 입력받아 뒤쪽 토큰부터 순차적으로 DB를 조회합니다.
    1. 뒤에서부터 토큰을 하나씩 확인하며 최초로 검색 결과가 존재하는 토큰을 찾습니다. (SELECT)
    2. 결과가 1개 이상 확보되면, 남은 앞쪽 토큰들을 이용해 메모리 내에서 필터링합니다. (Filter)
    """
    if not address:
        return None

    # ---------------------------------------------------------
    # 0. 주소 전처리
    # ---------------------------------------------------------
    address = normalize_address_for_lawd(address)
    if not address:
        return None

    # 공백 기준으로 전체 토큰화
    tokens = [t.strip() for t in address.split() if t.strip()]
    if not tokens:
        return None

    conn = get_conn(db_path)
    try:
        candidate_rows = []
        last_searched_idx = -1

        # --- Step 1: 결과가 나올 때까지 뒤에서부터 토큰별 DB 조회 ---
        for i in range(len(tokens) - 1, -1, -1):
            token = tokens[i]
            sql = f"SELECT lawd_cd, lawd_name FROM {TABLE_NAME} WHERE lawd_name LIKE ?"
            cur = conn.execute(sql, (f"%{token}%",))
            candidate_rows = cur.fetchall()

            if candidate_rows:
                # 결과가 있는 토큰을 찾았으므로 해당 위치 저장 후 중단
                last_searched_idx = i
                break

        if not candidate_rows:
            return None  # 모든 토큰을 뒤져도 결과가 없으면 종료

        # --- 최종 결과 확정 로직 ---
        final_row = None

        # 결과가 1개면 즉시 확정
        if len(candidate_rows) == 1:
            final_row = candidate_rows[0]
        else:
            # --- Step 2: 결과가 여러 개일 경우, 남은 앞쪽 토큰들로 결과 내 필터링 ---
            remaining_tokens = tokens[:last_searched_idx][::-1]

            for token in remaining_tokens:
                filtered_rows = [row for row in candidate_rows if token in row[1]]
                if filtered_rows:
                    candidate_rows = filtered_rows
                if len(candidate_rows) == 1:
                    break

            final_row = candidate_rows[0]

        # --- 데이터 준비 (예시 데이터 기준) ---
        res_lawd_cd = final_row[0]  # 예: "4157010300"
        res_lawd_name = final_row[1]  # 예: "경기도 수원시 권선구 호매실동"

        # 공백 기준으로 이름 분리
        name_parts = res_lawd_name.split()

        # 1. lawd_name: 전체 명칭
        lawd_name = res_lawd_name

        # 2. region: 첫 번째 단어 (시/도)
        region = name_parts[0] if len(name_parts) > 0 else ""

        # 3. sigungu_code: lawd_cd의 앞 5자리
        sigungu_code = res_lawd_cd[:5]

        # 4. sigungu_name: 중간 단어들을 합침 (시/군/구)
        # 첫 번째(시/도)와 마지막(읍/면/동)을 제외한 나머지 부분을 합칩니다.
        sigungu_name = " ".join(name_parts[1:-1])

        # 5. umd_name & eub_myeon_dong: 마지막 단어
        umd_name = name_parts[-1] if len(name_parts) > 1 else ""

        # ---------------------------------------------------------
        # 리턴 데이터 조립 및 필드 설명
        # ---------------------------------------------------------
        # 1. lawd_cd: 전체 법정동 코드 (예: 4157010300)
        # 2. lawd_name: 전체 주소 명칭 (예: 경기도 수원시 권선구 호매실동)
        # 3. region: 광역 지자체 이름 (예: 경기도, 경상북도)
        # 4. sigungu_code: 법정동 코드 앞 5자리 (예: 41570)
        # 5. sigungu_name: 기초 지자체 이름 (예: 수원시 권선구, 하동군)
        # 6. umd_name: 가장 하위 행정구역 읍/면/동  명칭 (예: 호매실동, 진교면)
        # ---------------------------------------------------------
        return {
            "lawd_cd": res_lawd_cd,
            "lawd_name": res_lawd_name,
            "region": region,
            "sigungu_code": sigungu_code,
            "sigungu_name": sigungu_name,
            "umd_name": umd_name
        }
    finally:
        conn.close()

# ==========================
# 3-2) lawd_code 테이블 전체 조회
def get_lawd_by_codes(db_path: str = DB_PATH) -> List[Dict[str, str]]:
    """
    lawd_code 테이블에서 법정동 코드와 이름을 전체 조회하여 리턴합니다.
    입력 조건 없이 모든 레코드를 가져옵니다.
    반환: [{"lawd_cd": "...", "lawd_name": "..."}, ...]
    """

    conn = get_conn(db_path)
    try:
        # WHERE 절 없이 전체 레코드를 조회합니다.
        sql = f"SELECT lawd_cd, lawd_name, batch_apt_yn, batch_villa_yn, batch_sanga_yn FROM {TABLE_NAME}"
        cur = conn.execute(sql)

        rows = cur.fetchall()

        # 결과를 [{"lawd_cd": "...", "lawd_name": "..."}] 형태로 변환
        result_list = [{"lawd_cd": row[0], "lawd_name": row[1], "batch_apt_yn": row[2], "batch_villa_yn": row[3], "batch_sanga_yn": row[4]} for row in rows]

        return result_list
    except Exception as e:
        print(f"DB 전체 조회 중 오류 발생: {e}")
        return []
    finally:
        conn.close()

# ==========================
# 4) 삭제 / 초기화 기능 추가
# ==========================
def drop_lawd_table(db_path: str = DB_PATH) -> None:
    """lawd_code 테이블 자체를 완전히 삭제(DROP TABLE)."""
    conn = get_conn(db_path)
    try:
        conn.execute(f"DROP TABLE IF EXISTS {TABLE_NAME}")
        conn.commit()
        print(f"[DROP] {TABLE_NAME} 테이블이 삭제되었습니다.")
    finally:
        conn.close()


# ==========================
# 5) land_batch_yn 업데이트 (단일 lawd_cd)
# ==========================
def update_land_batch_yn_single(lawd_cd: str, trade_type: str, yn: str, db_path: str = DB_PATH) -> int:
    """
    주어진 단일 lawd_cd에 해당하는 레코드의 특정 거래 유형(APT/VILLA/SANGA) 배치 처리 여부 필드(batch_..._yn)를 업데이트합니다.

    Args:
        lawd_cd: 업데이트할 단일 법정동 코드(lawd_cd).
        trade_type: 업데이트할 거래 유형 ('APT', 'VILLA', 'SANGA'). 대소문자 구분 없음.
        yn: 설정할 배치 처리 여부 값 ('Y' 또는 'N').
        db_path: SQLite DB 파일 경로.

    Returns:
        업데이트된 행 수 (0 또는 1).
    """
    if not lawd_cd:
        return 0

    # yn 값 유효성 검사
    upper_yn = yn.upper()
    if upper_yn not in ('Y', 'N'):
        print(f"경고: 유효하지 않은 yn 값 '{yn}'이 입력되었습니다. ('Y' 또는 'N' 필요)")
        return 0

    # trade_type에 따라 업데이트할 필드 결정
    upper_type = trade_type.upper()
    if upper_type == 'APT':
        target_field = 'batch_apt_yn'
    elif upper_type == 'VILLA':
        target_field = 'batch_villa_yn'
    elif upper_type == 'SANGA':
        target_field = 'batch_sanga_yn'
    else:
        print(f"경고: 유효하지 않은 거래 유형 '{trade_type}'이 입력되었습니다. ('APT', 'VILLA', 'SANGA' 필요)")
        return 0


    conn = get_conn(db_path)
    try:
        # 동적으로 필드 이름을 사용하여 UPDATE 쿼리 생성
        sql = f"""
        UPDATE {TABLE_NAME}
        SET {target_field} = ?
        WHERE lawd_cd = ?;
        """

        # 쿼리 실행: 첫 번째 매개변수는 yn 값, 두 번째는 lawd_cd
        cur = conn.execute(sql, (upper_yn, str(lawd_cd).strip()))

        # 업데이트된 행 수 확인
        updated_rows = cur.rowcount
        conn.commit()

        return updated_rows
    except Exception as e:
        conn.rollback()
        print(f"단일 lawd_cd 업데이트 중 오류 발생: {e}")
        return 0
    finally:
        conn.close()

# ==========================
# 5) land_batch_yn 멀티 업데이트 (APT / VILLA / SANGA)
# ==========================
def update_land_batch_yn_multi(
    lawd_cd: str,
    apt: str = None,
    villa: str = None,
    sanga: str = None,
    db_path: str = DB_PATH
) -> int:
    """
    한 번의 호출로 APT / VILLA / SANGA 필드를 선택적 업데이트.

    Args:
        lawd_cd (str): 업데이트할 단일 법정동 코드
        apt (str): 'Y'/'N' 또는 None
        villa (str): 'Y'/'N' 또는 None
        sanga (str): 'Y'/'N' 또는 None
    """

    if not lawd_cd:
        return 0

    updates = []
    values = []

    # 유효성 검사 + 업데이트 목록 생성
    if apt is not None:
        if apt.upper() not in ("Y", "N"):
            print(f"❌ APT yn값 오류: {apt}")
        else:
            updates.append("batch_apt_yn = ?")
            values.append(apt.upper())

    if villa is not None:
        if villa.upper() not in ("Y", "N"):
            print(f"❌ VILLA yn값 오류: {villa}")
        else:
            updates.append("batch_villa_yn = ?")
            values.append(villa.upper())

    if sanga is not None:
        if sanga.upper() not in ("Y", "N"):
            print(f"❌ SANGA yn값 오류: {sanga}")
        else:
            updates.append("batch_sanga_yn = ?")
            values.append(sanga.upper())

    # 업데이트할 값이 없는 경우
    if not updates:
        print("⚠️ 업데이트할 배치 필드가 없습니다.")
        return 0

    set_clause = ", ".join(updates)

    conn = get_conn(db_path)
    try:
        sql = f"""
            UPDATE {TABLE_NAME}
            SET {set_clause}
            WHERE lawd_cd = ?;
        """
        values.append(str(lawd_cd).strip())

        cur = conn.execute(sql, values)
        conn.commit()
        return cur.rowcount

    except Exception as e:
        conn.rollback()
        print(f"❌ 멀티 업데이트 오류: {e}")
        return 0

    finally:
        conn.close()


def normalize_address_for_lawd(address: str) -> str:
    """
    법정동 검색용 주소 정규화

    처리 예:
    1) 인천 남동구 구월동 1457, 2층210호 (구월동,이노프라자) 외 1개호
       -> 인천 남동구 구월동 1457

    2) 서울특별시 광진구 능동 177-3 빌라헤르메스 지층103호 외 2필지
       -> 서울특별시 광진구 능동 177-3
    """
    if not address:
        return ""

    addr = address.strip()

    # 1. 괄호 안 제거
    addr = re.sub(r"\([^)]*\)", " ", addr)

    # 2. "외 1개호", "외 2필지", "외 3호" 제거
    addr = re.sub(r"\s*외\s*\d+\s*(개호|필지|호)?", " ", addr)

    # 3. 쉼표는 공백으로 변경
    addr = addr.replace(",", " ")

    # 4. 연속 공백 정리
    addr = re.sub(r"\s+", " ", addr).strip()

    if not addr:
        return ""

    tokens = addr.split()
    cleaned_tokens = []

    found_umd = False  # 동/읍/면/리 찾았는지
    found_jibun = False  # 지번 찾았는지

    # 지번 패턴: 1457 / 177-3 / 산12 / 산12-3
    jibun_pattern = re.compile(r"^(산)?\d+(?:-\d+)?$")

    # 읍/면/동/리 패턴
    umd_pattern = re.compile(r"(동|읍|면|리)$")

    for token in tokens:
        # 이미 지번까지 확보했으면 뒤는 버림
        if found_jibun:
            break

        cleaned_tokens.append(token)

        # 아직 읍/면/동/리를 못 찾은 상태에서 찾으면 표시
        if not found_umd and umd_pattern.search(token):
            found_umd = True
            continue

        # 읍/면/동/리 찾은 뒤 첫 지번이 나오면 여기까지 채택
        if found_umd and jibun_pattern.match(token):
            found_jibun = True
            break

    # 혹시 지번이 없더라도, 최소한 앞부분 행정주소만 사용
    normalized = " ".join(cleaned_tokens).strip()
    return normalized


# ==========================
# 사용 예시
# ==========================
if __name__ == "__main__":
    # 1) 테이블 생성
    #init_lawd_db()

    # 4) 테이블/데이터 삭제 예시
    # drop_lawd_table()     # 테이블 전체 삭제

    # 2) TXT 로드 (예: /path/to/법정동코드.txt)
    #    헤더: 법정동코드\t법정동명\t폐지여부
    # sample_txt = "법정동코드.txt"
    # try:
    #     n = load_lawd_from_txt(sample_txt)
    #     print(f"[LOAD] 적재 행수: {n}")
    # except FileNotFoundError:
    #     print(f"[SKIP] 파일 없음: {sample_txt}")
    #
    # # 3) 코드로 단건 조회
    # res = get_lawd_by_code("1111010300")
    # print("[READ]", res)

    print("\n--- [TEST] 결과 내 검색 로직 테스트 ---")

    # 케이스 1: '장기' 검색 시 김포시와 포항시가 나오지만, '김포시' 토큰으로 필터링됨
    case1 = get_lawd_by_name("경기도 김포시 장기동 123")
    print(f"결과 1 (김포 장기): {case1}")

    # 케이스 2: 숫자가 섞인 주소 처리
    case2 = get_lawd_by_name("경기도 김포시 운양동 611")
    print(f"결과 2 (운양동): {case2}")

    # 케이스 3: 단순 동 이름만 입력
    case3 = get_lawd_by_name("청운동")
    print(f"결과 3 (청운동): {case3}")

    case3 = get_lawd_by_name("서울특별시 중구 남대문로4가")
    print(f"결과 3 (남대문로4가): {case3}")

    case4 = get_lawd_by_name("인천 남동구 구월동 1457, 2층210호 (구월동,이노프라자) 외 1개호 ")
    print(f"결과 4 (구월동): {case4}")

    case5 = get_lawd_by_name("서울특별시 광진구 능동 177-3 빌라헤르메스 지층103호 외 2필지")
    print(f"결과 5 (능동): {case5}")

    case6 = get_lawd_by_name("인천광역시 남동구 만수동 841-27, 대명빌라 5동 지층 1호 ")
    print(f"결과 5 (테스트): {case6}")