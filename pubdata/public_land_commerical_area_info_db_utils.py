# -*- coding: utf-8 -*-
import os
import csv
import glob
import unicodedata
import requests
import sqlite3
from config import PUBLIC_BASE_PATH

DB_PATH = os.path.join(PUBLIC_BASE_PATH, "public_commerical_area_data.db")
TABLE_NAME = "commercial_area_info"

API_URL = "https://apis.data.go.kr/B553077/api/open/sdsc2/storeListInDong"
SERVICE_KEY = "B2BtWbuZVFz/EJoLsrDa6corOwSR4SsGwjBKzK2WJQ3JVwRMIUoXOGY3BHXrxZq78nP+ECsW5wB4TEwbgxS2PA=="

# =========================
# DB 연결
# =========================
def get_conn(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

# =========================
# 테이블 생성 (상권정보)
# =========================
def init_db(db_path: str = DB_PATH) -> None:
    """
    상권정보 테이블 생성
    - bizesId를 PK로 사용 (중복방지)
    - 상권 분석용 핵심 인덱스 포함
    """

    ddl = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        -- =========================
        -- 기준 정보
        -- =========================
        stdrYm TEXT,                -- 기준년월 (YYYYMM)
        
        -- =========================
        -- 기본 정보
        -- =========================
        bizesId TEXT PRIMARY KEY,   -- 상가업소번호 (고유키)
        bizesNm TEXT,               -- 상호명
        brchNm TEXT,                -- 지점명

        -- =========================
        -- 업종 분류
        -- =========================
        indsLclsCd TEXT,            -- 대분류 코드
        indsLclsNm TEXT,            -- 대분류명
        indsMclsCd TEXT,            -- 중분류 코드
        indsMclsNm TEXT,            -- 중분류명
        indsSclsCd TEXT,            -- 소분류 코드
        indsSclsNm TEXT,            -- 소분류명

        ksicCd TEXT,                -- 표준산업 코드
        ksicNm TEXT,                -- 표준산업명

        -- =========================
        -- 행정구역
        -- =========================
        ctprvnCd TEXT,              -- 시도코드
        ctprvnNm TEXT,              -- 시도명
        signguCd TEXT,              -- 시군구코드
        signguNm TEXT,              -- 시군구명
        adongCd TEXT,               -- 행정동코드
        adongNm TEXT,               -- 행정동명
        ldongCd TEXT,               -- 법정동코드
        ldongNm TEXT,               -- 법정동명

        -- =========================
        -- 지번 주소
        -- =========================
        lnoCd TEXT,                 -- PNU
        plotSctCd TEXT,             -- 대지구분코드
        plotSctNm TEXT,             -- 대지구분명
        lnoMnno TEXT,               -- 본번
        lnoSlno TEXT,               -- 부번
        lnoAdr TEXT,                -- 지번주소

        -- =========================
        -- 도로명 주소
        -- =========================
        rdnmCd TEXT,                -- 도로명코드
        rdnm TEXT,                  -- 도로명
        bldMnno TEXT,               -- 건물본번
        bldSlno TEXT,               -- 건물부번
        bldMngNo TEXT,              -- 건물관리번호
        bldNm TEXT,                 -- 건물명
        rdnmAdr TEXT,               -- 도로명주소

        -- =========================
        -- 기타
        -- =========================
        oldZipcd TEXT,              -- 구우편번호
        newZipcd TEXT,              -- 신우편번호
        dongNo TEXT,                -- 동
        flrNo TEXT,                 -- 층
        hoNo TEXT,                  -- 호

        -- =========================
        -- 좌표
        -- =========================
        lon TEXT,                   -- 경도
        lat TEXT                    -- 위도
    );
    """

    # =========================
    # 인덱스 (성능 핵심)
    # =========================
    # 1. 동 + 년월 (핵심 분석용)
    idx1 = f"""
    CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_ldong_ym
    ON {TABLE_NAME}(ldongCd, stdrYm);
    """

    # 2. 업종 분석용
    # idx2 = f"""
    # CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_inds
    # ON {TABLE_NAME}(indsMclsCd);
    # """

    conn = get_conn(db_path)
    try:
        conn.execute(ddl)
        conn.execute(idx1)
        conn.commit()
    finally:
        conn.close()


# =========================
# DB 저장
# =========================
def insert_data(items, stdrYm, db_path: str = DB_PATH):
    conn = get_conn(db_path)
    cur = conn.cursor()

    for row in items:
        # 1. 각 행(row) 딕셔너리에 stdrYm 값을 강제로 주입합니다.
        row['stdrYm'] = stdrYm

        cur.execute(f"""
        INSERT OR REPLACE INTO {TABLE_NAME} VALUES (
            :stdrYm,
            :bizesId,:bizesNm,:brchNm,
            :indsLclsCd,:indsLclsNm,
            :indsMclsCd,:indsMclsNm,
            :indsSclsCd,:indsSclsNm,
            :ksicCd,:ksicNm,
            :ctprvnCd,:ctprvnNm,
            :signguCd,:signguNm,
            :adongCd,:adongNm,
            :ldongCd,:ldongNm,
            :lnoCd,
            :plotSctCd,:plotSctNm,
            :lnoMnno,:lnoSlno,
            :lnoAdr,
            :rdnmCd,:rdnm,
            :bldMnno,:bldSlno,
            :bldMngNo,:bldNm,
            :rdnmAdr,
            :oldZipcd,:newZipcd,
            :dongNo,:flrNo,:hoNo,
            :lon,:lat
        )
        """, row)

    conn.commit()
    conn.close()


def delete_all_data(db_path: str = DB_PATH):
    """
    지정한 테이블의 모든 데이터를 삭제합니다.
    """
    conn = get_conn(db_path)
    cur = conn.cursor()

    # 1. 모든 행 삭제 (가장 일반적인 방식)
    sql = f"DELETE FROM {TABLE_NAME}"

    try:
        cur.execute(sql)

        # 2. SQLite에서 삭제 후 파일 크기 최적화를 원할 경우 (선택 사항)
        # cur.execute("VACUUM")

        conn.commit()
        print(f"[{TABLE_NAME}] 테이블의 모든 데이터({cur.rowcount}건)가 삭제되었습니다.")
    except Exception as e:
        print(f"전체 삭제 중 오류 발생: {e}")
    finally:
        conn.close()

def delete_existing_data(stdrYm, dong_code, db_path: str = DB_PATH):
    """
    특정 기준년월과 행정동(또는 법정동) 코드를 기준으로 기존 데이터를 삭제합니다.
    """
    conn = get_conn(db_path)
    cur = conn.cursor()

    # 행정동(adongCd) 기준 삭제를 기본으로 합니다.
    # 만약 법정동 기준이라면 컬럼명을 ldongCd로 변경하세요.
    sql = f"DELETE FROM {TABLE_NAME} WHERE stdrYm = ? AND adongCd = ?"

    try:
        cur.execute(sql, (stdrYm, dong_code))
        conn.commit()
        print(f"[{stdrYm} / {dong_code}] 기존 데이터 삭제 완료 (삭제건수: {cur.rowcount})")
    except Exception as e:
        print(f"삭제 중 오류 발생: {e}")
    finally:
        conn.close()


# =========================
# API 호출 (JSON)
# =========================
def call_api_paged(divId="", ldongCd="9301", end_page=5):
    """
    페이지별로 API를 호출하고, 호출 성공 시 즉시 DB에 저장합니다.
    """
    total_count = 0
    final_stdrYm = ""

    for page in range(1, end_page + 1):
        params = {
            "divId": divId,
            "key": ldongCd,
            "numOfRows": 999,
            "pageNo": page,
            "type": "json",
            "serviceKey": SERVICE_KEY
        }

        try:
            print(f">>> {page}페이지 요청 중...")
            res = requests.get(API_URL, params=params, timeout=30)
            res.raise_for_status()

            data = res.json()
            stdrYm, items = parse_json(data)

            if items:
                # [핵심] 페이지 단위로 즉시 DB 저장
                insert_data(items, stdrYm)

                total_count += len(items)
                final_stdrYm = stdrYm
                print(f"    - {page}페이지 저장 완료: {len(items)}건 (누적: {total_count}건)")
            else:
                print(f"    - {page}페이지에 데이터가 없습니다. 수집을 중단합니다.")
                break

        except Exception as e:
            print(f"    - {page}페이지 처리 중 오류 발생: {e}")
            break

    return final_stdrYm, total_count

# =========================
# JSON 파싱
# =========================
def parse_json(json_data):
    # 1. 'response' 키 없이 바로 header와 body에 접근합니다.
    header = json_data.get("header", {})
    body = json_data.get("body", {})

    # header 정보 추출
    stdrYm = header.get("stdrYm", "")
    resultCode = header.get("resultCode", "")
    resultMsg = header.get("resultMsg", "")

    print(f"기준년월: {stdrYm}")
    print(f"결과코드: {resultCode}")
    print(f"결과메시지: {resultMsg}")

    # 2. body 내부의 items를 가져옵니다.
    items = body.get("items", [])

    # items가 dict 1건으로 내려오는 경우(단일 데이터)를 대비해 리스트로 변환
    if isinstance(items, dict):
        items = [items]

    normalized_items = []
    columns = [
        "bizesId", "bizesNm", "brchNm", "indsLclsCd", "indsLclsNm",
        "indsMclsCd", "indsMclsNm", "indsSclsCd", "indsSclsNm",
        "ksicCd", "ksicNm", "ctprvnCd", "ctprvnNm", "signguCd", "signguNm",
        "adongCd", "adongNm", "ldongCd", "ldongNm", "lnoCd",
        "plotSctCd", "plotSctNm", "lnoMnno", "lnoSlno", "lnoAdr",
        "rdnmCd", "rdnm", "bldMnno", "bldSlno", "bldMngNo", "bldNm",
        "rdnmAdr", "oldZipcd", "newZipcd", "dongNo", "flrNo", "hoNo",
        "lon", "lat"
    ]

    for item in items:
        row = {}
        for col in columns:
            # 값이 None일 경우 빈 문자열로 처리
            value = item.get(col, "")
            row[col] = "" if value is None else str(value)
        normalized_items.append(row)

    return stdrYm, normalized_items


# =========================
# 법정도코드로 조회처리
# =========================
def search_by_ldong(ldong_code: str, limit: int = 999):
    """
    법정동 코드로 저장된 데이터를 검색하여 딕셔너리 리스트(JSON 형태)로 반환합니다.
    """
    conn = get_conn()
    cur = conn.cursor()

    sql = f"""
        SELECT stdrYm, bizesId, bizesNm, adongCd, adongNm, ldongCd, ldongNm, 
               rdnmAdr, indsLclsNm, indsMclsNm, indsSclsNm, lon, lat
        FROM {TABLE_NAME}
        WHERE ldongCd = ?
        LIMIT ?
    """

    try:
        cur.execute(sql, (ldong_code, limit))
        rows = cur.fetchall()

        if not rows:
            print(f"[{ldong_code}] 검색된 데이터가 없습니다.")
            return []

        # 튜플을 딕셔너리로 변환 (JSON 구조화)
        results = []
        for r in rows:
            results.append({
                "stdrYm": r[0],
                "bizesId": r[1],
                "bizesNm": r[2],
                "adongCd": r[3],
                "adongNm": r[4],
                "ldongCd": r[5],
                "ldongNm": r[6],
                "rdnmAdr": r[7],
                "indsLclsNm": r[8],
                "indsMclsNm": r[9],
                "indsSclsNm": r[10],
                "lon": float(r[11]) if r[11] else None,
                "lat": float(r[12]) if r[12] else None
            })

        print(f"🔍 [조회 완료] 법정동 {ldong_code}: {len(results)}건")
        return results

    except Exception as e:
        print(f"조회 중 오류 발생: {e}")
        return []
    finally:
        conn.close()


# =========================
# CSV 처리
# =========================
def process_csv_by_region(region_name: str):
    """
    1. commerical_area_data 폴더 내에서 지역명이 포함된 CSV 파일을 찾아 저장합니다.
    2. 파일명 예시: 소상공인시장진흥공단_상가(상권)정보_제주_202512.csv
    """
    # 3번 조건: 디렉토리 설정
    base_dir = os.path.join(os.getcwd(), "commerical_area_data")
    # 디버깅용: 실제 찾는 경로를 출력해봅니다.
    print(f"[*] 탐색 경로: {base_dir}")

    if not os.path.exists(base_dir):
        print(f"[오류] 폴더가 존재하지 않습니다: {base_dir}")
        return None, 0

    # 2. 검색어(지역명)를 NFC(완성형)로 표준화
    search_name = unicodedata.normalize('NFC', region_name)

    all_files = os.listdir(base_dir)
    target_file_name = None

    # 3. 파일 목록 탐색
    for f_name in all_files:
        # 파일명을 NFC로 변환하여 비교 (OS간 호환성 핵심)
        normalized_f_name = unicodedata.normalize('NFC', f_name)

        # 대소문자 무시 및 한글 포함 여부 체크
        if search_name.lower() in normalized_f_name.lower() and f_name.lower().endswith(".csv"):
            target_file_name = f_name
            break

    if not target_file_name:
        print(f"[오류] '{region_name}' 문구가 포함된 파일을 찾을 수 없습니다.")
        return "N/A", 0

    target_file_path = os.path.join(base_dir, target_file_name)
    print(f"[CSV 발견] 작업 파일: {target_file_name}")

    # 4. 파일명에서 기준년월(stdrYm) 추출 (예: 202512)
    # 파일명이 '..._강원_202512.csv' 형태라면 뒤에서 10자~4자 사이가 날짜입니다.
    import re
    date_match = re.search(r'\d{6}', target_file_name)
    stdrYm = date_match.group() if date_match else "202512"

    total_count = 0
    batch_items = []

    try:
        with open(target_file_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # CSV 헤더명 -> DB 컬럼명 변환 (API와 동일하게 맞춤)
                item = {
                    "bizesId": row.get("상가업소번호", ""),
                    "bizesNm": row.get("상호명", ""),
                    "brchNm": row.get("지점명", ""),
                    "indsLclsCd": row.get("상권업종대분류코드", ""),
                    "indsLclsNm": row.get("상권업종대분류명", ""),
                    "indsMclsCd": row.get("상권업종중분류코드", ""),
                    "indsMclsNm": row.get("상권업종중분류명", ""),
                    "indsSclsCd": row.get("상권업종소분류코드", ""),
                    "indsSclsNm": row.get("상권업종소분류명", ""),
                    "ksicCd": row.get("표준산업분류코드", ""),
                    "ksicNm": row.get("표준산업분류명", ""),
                    "ctprvnCd": row.get("시도코드", ""),
                    "ctprvnNm": row.get("시도명", ""),
                    "signguCd": row.get("시군구코드", ""),
                    "signguNm": row.get("시군구명", ""),
                    "adongCd": row.get("행정동코드", ""),
                    "adongNm": row.get("행정동명", ""),
                    "ldongCd": row.get("법정동코드", ""),
                    "ldongNm": row.get("법정동명", ""),
                    "lnoCd": row.get("지번코드", ""),
                    "plotSctCd": row.get("대지구분코드", ""),
                    "plotSctNm": row.get("대지구분명", ""),
                    "lnoMnno": row.get("지번본번지", ""),
                    "lnoSlno": row.get("지번부번지", ""),
                    "lnoAdr": row.get("지번주소", ""),
                    "rdnmCd": row.get("도로명코드", ""),
                    "rdnm": row.get("도로명", ""),
                    "bldMnno": row.get("건물본번지", ""),
                    "bldSlno": row.get("건물부번지", ""),
                    "bldMngNo": row.get("건물관리번호", ""),
                    "bldNm": row.get("건물명", ""),
                    "rdnmAdr": row.get("도로명주소", ""),
                    "oldZipcd": row.get("구우편번호", ""),
                    "newZipcd": row.get("신우편번호", ""),
                    "dongNo": row.get("동정보", ""),
                    "flrNo": row.get("층정보", ""),
                    "hoNo": row.get("호정보", ""),
                    "lon": row.get("경도", ""),
                    "lat": row.get("위도", "")
                }
                batch_items.append(item)

                # 1000건마다 DB에 저장하여 속도와 안정성 확보
                if len(batch_items) >= 1000:
                    insert_data(batch_items, stdrYm)
                    total_count += len(batch_items)
                    print(f" >>> [CSV 저장 중] {total_count}건 처리 완료...")
                    batch_items = []

            # 남은 데이터 저장
            if batch_items:
                insert_data(batch_items, stdrYm)
                total_count += len(batch_items)

        print(f"[CSV 완료] {region_name} 지역 총 {total_count}건 저장 성공.")
        return stdrYm, total_count

    except Exception as e:
        print(f"[오류] CSV 처리 중 문제 발생: {e}")
        return stdrYm, 0

# =========================
# MAIN 테스트
# =========================
def main():
    print("=== 상권정보(JSON) 수집 시작 ===")
    # 실행 모드 설정 ("API" 또는 "CSV")
    MODE = "CSV"

    # 리스트 형태로 여러 지역을 입력합니다.
    #TARGET_REGIONS = ["강원", "경기", "경남", "경북", "광주", "대구", "대전", "부산", "서울", "세종", "울산", "인천", "전남", "전북", "제주", "충남", "충북"]
    TARGET_REGIONS = ["경기"]

    # init_db()
    #
    # # 1. 수집 전 기존 데이터를 모두 삭제하고 싶다면 여기서 한 번 수행 (선택 사항)
    # delete_all_data()
    #
    # total_all_regions = 0
    # final_stdrYm = "N/A"
    #
    # if MODE.upper() == "API":
    #     print("=== [모드: API] 실시간 수집 시작 ===")
    #     final_stdrYm, total_all_regions = call_api_paged(divId="", ldongCd="9301", end_page=5)
    #
    # else:
    #     print(f"=== [모드: CSV] 로컬 파일 다중 처리 시작 ({', '.join(TARGET_REGIONS)}) ===")
    #
    #     for region in TARGET_REGIONS:
    #         print(f"\n[*] '{region}' 지역 처리 중...")
    #         # process_csv_by_region이 (stdrYm, count)를 반환하도록 수정된 버전을 사용해야 합니다.
    #         res_ym, res_count = process_csv_by_region(region)
    #
    #         if res_count > 0:
    #             total_all_regions += res_count
    #             final_stdrYm = res_ym  # 마지막으로 성공한 지역의 기준년월 저장
    #         else:
    #             print(f"[-] '{region}' 지역은 파일을 찾지 못했거나 데이터가 없습니다.")
    #
    # # 3. 최종 공통 결과 출력
    # print("\n" + "=" * 50)
    # if total_all_regions > 0:
    #     print(f"최종 합계 보고")
    #     print(f"- 기준월: {final_stdrYm}")
    #     print(f"- 대상 지역: {', '.join(TARGET_REGIONS)}")
    #     print(f"- 총 저장 건수: {total_all_regions:,}건")  # 천단위 콤마 표기
    # else:
    #     print("수집 및 저장된 데이터가 하나도 없습니다.")
    # print("=" * 50)
    # print("=== 모든 작업 완료 ===")

    # 3. [추가된 기능] 법정동 코드로 검색 테스트
    # 예시: 인천 부평동(2823710100), 김포시 운양동(4157010300) 또는 API에서 방금 넣은 데이터의 법정동 코드 사용
    test_ldong = "4157010300"

    # 데이터 조회 호출
    search_results = search_by_ldong(test_ldong, limit=50)

    print("-" * 50)
    if search_results:
        print(f"✅ 총 {len(search_results)}개의 데이터를 찾았습니다.")

        # JSON 형태의 데이터 출력 테스트
        for item in search_results:
            print(f"[{item['stdrYm']}] {item['bizesNm']} | {item['indsSclsNm']} | {item['rdnmAdr']} | (경도: {item['lon']}, 위도: {item['lat']})")
    else:
        print("❌ 표시할 데이터가 없습니다. 먼저 수집(API/CSV)을 진행하세요.")

    print("-" * 50)
    print("=== 작업 완료 ===")

if __name__ == "__main__":
    main()