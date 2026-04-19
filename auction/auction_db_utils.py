import os
from datetime import datetime
import sqlite3
import re

from common.vworld_utils import VWorldGeocoding
#
from config import AUCTION_DB_PATH, MAP_API_KEY

# 공통 변수 설정
CSV_FILENAME = "auction_data.csv"
DB_FILENAME = os.path.join(AUCTION_DB_PATH, "auction_data.db")
TABLE_NAME = "auction_data"

def create_auction_table():
    """
    auction_data 테이블을 생성합니다.
    case_number를 PRIMARY KEY로 지정하고, eub_myeon_dong 컬럼에 인덱스를 생성합니다.
    테이블이 이미 존재하면 아무 메시지도 출력하지 않습니다.
    """
    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()

    # 테이블 존재 여부 확인
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (TABLE_NAME,))
    table_exists = cursor.fetchone() is not None
    if not table_exists:
        cursor.execute(f"""
            CREATE TABLE {TABLE_NAME} (
                case_number TEXT,
                category TEXT,
                address1 TEXT,
                address2 TEXT,
                region TEXT,
                sigungu_code TEXT,
                sigungu_name TEXT,
                eub_myeon_dong TEXT,
                building TEXT,
                floor TEXT,
                building_m2 TEXT,
                building_py TEXT,
                land_m2 TEXT,
                land_py TEXT,
                appraisal_price INTEGER,
                min_price INTEGER,
                sale_price INTEGER,
                min_percent TEXT,
                sale_percent TEXT,
                pydanga_appraisal TEXT,
                pydanga_min TEXT,
                pydanga_sale TEXT,
                sales_date TEXT,
                dangi_name TEXT,
                extra_info TEXT,
                latitude TEXT,
                longitude TEXT
            )
        """)
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_eub_myeon_dong ON {TABLE_NAME} (eub_myeon_dong)")
        conn.commit()
        # 테이블과 인덱스가 새로 생성되었을 경우에만 메시지 출력 (아래 두 줄을 주석 처리하면 항상 출력하지 않음)
        print(f"테이블 '{TABLE_NAME}' 생성 완료 (case_number PRIMARY KEY, eub_myeon_dong 인덱스 포함).")
    # 테이블이 이미 존재하면 아무것도 출력하지 않음
    conn.close()


# 멀티레코드 입력처리
def auction_save_to_sqlite(data):
    """
    주어진 data (리스트 내의 dict들)를 SQLite 데이터베이스에 저장하는 함수.
    각 레코드의 case_number를 기준으로 기존에 존재하지 않을 때만 auction_insert_single을 호출하여 저장합니다.
    """
    if not data:
        print("저장할 데이터가 없습니다.")
        return

    # 테이블및 인덱스 없으면 생성
    create_auction_table()

    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()
    for entry in data:
        #
        auction_insert_single(entry)
        #
        # 이미 해당 case_number의 레코드가 존재하는지 체크합니다.
        # existing = auction_select_single(entry.get("case_number"))
        # if existing is None:
        #     auction_insert_single(entry)
        # else:
        #     print(f"레코드 {entry.get('case_number')} 는 이미 존재하여 삽입하지 않음.")

    print(f"SQLite DB({DB_FILENAME})에 {len(data)} 건의 데이터 처리 완료.")

def auction_drop_table():
    """
    DB_FILENAME에 정의된 SQLite 데이터베이스에서 TABLE_NAME에 해당하는 테이블을 삭제합니다.
    테이블이 존재하지 않으면 아무런 오류 없이 넘어갑니다.
    """
    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()
    cursor.execute(f"DROP TABLE IF EXISTS {TABLE_NAME}")
    conn.commit()
    conn.close()
    print(f"테이블 '{TABLE_NAME}' 삭제 완료.")

# ────────── 단일 레코드 처리 함수들 ──────────
def auction_insert_single(entry):
    """
    단일 레코드를 삽입합니다.
    :param entry: dict 형태의 레코드 데이터 (case_number가 반드시 포함되어야 함)
    """
    #create_auction_table()  # 테이블이 없으면 생성
    #
    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()
    insert_query = f"""INSERT INTO {TABLE_NAME} (
         case_number, category, address1, address2, region, sigungu_code, sigungu_name, 
         eub_myeon_dong, building, floor, building_m2, building_py, land_m2, land_py, 
         appraisal_price, min_price, sale_price, min_percent, sale_percent, 
         pydanga_appraisal, pydanga_min, pydanga_sale, sales_date, dangi_name, extra_info, latitude, longitude
         ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""
    try:
        cursor.execute(insert_query, (
            entry.get("case_number"),
            entry.get("category"),
            entry.get("address1"),
            entry.get("address2"),
            entry.get("region"),
            entry.get("sigungu_code"),
            entry.get("sigungu_name"),
            entry.get("eub_myeon_dong"),
            entry.get("building"),
            entry.get("floor"),
            entry.get("building_m2"),
            entry.get("building_py"),
            entry.get("land_m2"),
            entry.get("land_py"),
            entry.get("appraisal_price"),
            entry.get("min_price"),
            entry.get("sale_price"),
            entry.get("min_percent"),
            entry.get("sale_percent"),
            entry.get("pydanga_appraisal"),
            entry.get("pydanga_min"),
            entry.get("pydanga_sale"),
            entry.get("sales_date"),
            entry.get("dangi_name"),
            entry.get("extra_info"),
            entry.get("latitude"),
            entry.get("longitude")
        ))
        conn.commit()
        print("단일 레코드 삽입 완료.")
    except Exception as e:
        print("단일 레코드 삽입 오류:", e)
    finally:
        conn.close()

def auction_update_single(entry):
    """
    case_number를 기준으로 단일 레코드를 수정합니다.
    :param entry: dict 형태의 레코드 데이터 (수정할 값들과 case_number 포함)
    """
    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()
    update_query = f"""UPDATE {TABLE_NAME} SET
        category = ?,
        address1 = ?,
        address2 = ?,
        region = ?,
        sigungu_code = ?,
        sigungu_name = ?,
        eub_myeon_dong = ?,
        building = ?,
        floor = ?,
        building_m2 = ?,
        building_py = ?,
        land_m2 = ?,
        land_py = ?,
        appraisal_price = ?,
        min_price = ?,
        sale_price = ?,
        min_percent = ?,
        sale_percent = ?,
        pydanga_appraisal = ?,
        pydanga_min = ?,
        pydanga_sale = ?,
        sales_date = ?,
        dangi_name = ?,
        extra_info = ?,
        latitude = ?,
        longitude = ?
        WHERE case_number = ?
    """
    try:
        cursor.execute(update_query, (
            entry.get("category"),
            entry.get("address1"),
            entry.get("address2"),
            entry.get("region"),
            entry.get("sigungu_code"),
            entry.get("sigungu_name"),
            entry.get("eub_myeon_dong"),
            entry.get("building"),
            entry.get("floor"),
            entry.get("building_m2"),
            entry.get("building_py"),
            entry.get("land_m2"),
            entry.get("land_py"),
            entry.get("appraisal_price"),
            entry.get("min_price"),
            entry.get("sale_price"),
            entry.get("min_percent"),
            entry.get("sale_percent"),
            entry.get("pydanga_appraisal"),
            entry.get("pydanga_min"),
            entry.get("pydanga_sale"),
            entry.get("sales_date"),
            entry.get("dangi_name"),
            entry.get("extra_info"),
            entry.get("latitude"),
            entry.get("longitude"),
            entry.get("case_number")
        ))
        conn.commit()
        print("단일 레코드 수정 완료.")
    except Exception as e:
        print("단일 레코드 수정 오류:", e)
    finally:
        conn.close()

def auction_delete_single(case_number):
    """
    주어진 case_number에 해당하는 단일 레코드를 삭제합니다.
    :param case_number: 삭제할 레코드의 primary key 값
    """
    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()
    delete_query = f"DELETE FROM {TABLE_NAME} WHERE case_number = ?"
    try:
        cursor.execute(delete_query, (case_number,))
        conn.commit()
        print(f"레코드 {case_number} 삭제 완료.")
    except Exception as e:
        print("단일 레코드 삭제 오류:", e)
    finally:
        conn.close()

def auction_select_single(case_number):
    """
    주어진 case_number에 해당하는 단일 레코드를 조회하여 dict 형태로 반환합니다.
    :param case_number: 조회할 레코드의 primary key 값
    :return: dict 형태의 레코드 또는 None
    """
    conn = sqlite3.connect(DB_FILENAME)
    conn.row_factory = sqlite3.Row  # 각 행을 dict처럼 취급
    cursor = conn.cursor()
    select_query = f"SELECT * FROM {TABLE_NAME} WHERE case_number = ?"
    try:
        cursor.execute(select_query, (case_number,))
        row = cursor.fetchone()
        if row:
            result = dict(row)
            print("단일 레코드 조회 완료.")
            return result
        else:
            print("해당 case_number의 레코드가 존재하지 않습니다.")
            return None
    except Exception as e:
        print("단일 레코드 조회 오류:", e)
        return None
    finally:
        conn.close()


def auction_read_db(lawdCd="", umdNm="", year_range="2", categories=None, dangiName=""):
    """
    SQLite DB(DB_FILENAME)에서 데이터를 읽어오며, 필터링 조건에 따라 반환합니다.

    year_range: "1"이면 현재년도 1월 1일부터 오늘까지, "2"이면 전년도 1월 1일부터 오늘까지
    """
    conn = sqlite3.connect(DB_FILENAME)
    conn.row_factory = sqlite3.Row  # 각 행을 dict처럼 취급
    cur = conn.cursor()
    query = f"SELECT * FROM {TABLE_NAME} WHERE 1=1"
    params = []

    if lawdCd:
        query += " AND sigungu_code LIKE ?"
        params.append(f"%{lawdCd}%")
    if umdNm:
        query += " AND eub_myeon_dong LIKE ?"
        params.append(f"%{umdNm}%")
    if categories:
        placeholders = ','.join('?' for _ in categories)
        query += f" AND category IN ({placeholders})"
        params.extend(categories)

    # 날짜 범위 필터 처리
    today = datetime.today()
    current_date = today.strftime("%Y-%m-%d")
    end_date = current_date  # 현재일
    if year_range == "1":
        start_date = f"{today.year}-01-01"
    elif year_range == "2":
        start_date = f"{today.year - 1}-01-01"
    else:
        start_date = None
        end_date = None

    if start_date and end_date:
        query += " AND sales_date BETWEEN ? AND ?"
        params.append(start_date)
        params.append(end_date)

    # 단지명  필터 처리
    if dangiName:
        query += " AND dangi_name LIKE ?"
        params.append(f"%{dangiName}%")

    # 정렬 (예: 최신 판매일자 내림차순)
    query += " ORDER BY sales_date DESC"

    cur.execute(query, params)
    rows = cur.fetchall()
    result = [dict(row) for row in rows]
    conn.close()
    return result

# region과 sigungu_name 조건을 사용하여 SQLite DB에서 데이터를 조회하는 함수
# 경기도, 김포시 조건으로 해당 동목록을 가져옴
def auction_read_by_region(sigungu_code="", eub_myeon_dong="", categories=None):
    """
    region, sigungu_name 및 category(멀티 선택 가능) 조건을 사용하여
    SQLite DB에서 데이터를 조회합니다.

    :param categories: ['아파트', '빌라'] 와 같은 형태의 리스트
    """
    conn = sqlite3.connect(DB_FILENAME)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    query = f"SELECT * FROM {TABLE_NAME} WHERE 1=1"
    params = []

    # 1. 시군구코드 필터(경기도-김포시)
    if sigungu_code:
        query += " AND sigungu_code LIKE ?"
        params.append(f"{sigungu_code}")

    # 2. 읍명동 필터
    if eub_myeon_dong:
        query += " AND eub_myeon_dong LIKE ?"
        params.append(f"%{eub_myeon_dong}%")

    # 3. category 멀티 필터 처리
    if categories and isinstance(categories, list):
        # 리스트 개수만큼 '?' 생성 (예: ?,?,?)
        placeholders = ', '.join(['?'] * len(categories))
        query += f" AND category IN ({placeholders})"
        params.extend(categories)

    # 최신순 정렬
    query += " ORDER BY sales_date DESC"

    try:
        cur.execute(query, params)
        rows = cur.fetchall()
        result = [dict(row) for row in rows]
        return result
    except Exception as e:
        print(f"조회 중 오류 발생: {e}")
        return []
    finally:
        conn.close()

# eub_myeon_dong 조건으로 조회하면서, latitude가 0.0 또는 비어있는 레코드 목록을 반환하는 함수
def auction_read_no_latlng_by_eub_myeon_dong(eub_myeon_dong: str):
    """
    eub_myeon_dong 조건으로 조회하면서,
    latitude가 0.0 또는 비어있는 레코드 목록을 반환합니다.

    예:
        eub_myeon_dong = '구월동'
        latitude = 0.0 인 데이터 조회
    """
    conn = sqlite3.connect(DB_FILENAME)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    query = f"""
          SELECT *
          FROM {TABLE_NAME}
          WHERE 1=1
            AND eub_myeon_dong LIKE ?
            AND (
                  latitude IS NULL
                  OR TRIM(CAST(latitude AS TEXT)) = ''
                  OR CAST(latitude AS REAL) = 0.0
                )
          ORDER BY sales_date DESC
      """
    params = [f"%{eub_myeon_dong}%"]

    try:
        cur.execute(query, params)
        rows = cur.fetchall()
        result = [dict(row) for row in rows]
        print(f"[조회완료] 위경도 미처리 건수: {len(result)} / eub_myeon_dong={eub_myeon_dong}")
        return result
    except Exception as e:
        print(f"위경도 미처리 목록 조회 오류: {e}")
        return []
    finally:
        conn.close()


# case_number 기준으로 latitude, longitude 만 업데이트하는 함수
def auction_update_latlng_by_case_number(case_number: str, latitude: float, longitude: float):
    """
    case_number 기준으로 latitude, longitude 만 업데이트합니다.
    """
    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()

    query = f"""
          UPDATE {TABLE_NAME}
          SET latitude = ?, longitude = ?
          WHERE case_number = ?
      """

    try:
        cursor.execute(query, (str(latitude), str(longitude), case_number))
        conn.commit()
        print(f"[업데이트완료] case_number={case_number}, lat={latitude}, lng={longitude}")
        return cursor.rowcount
    except Exception as e:
        print(f"위경도 업데이트 오류 (case_number={case_number}): {e}")
        return 0
    finally:
        conn.close()


# eub_myeon_dong 기준으로 latitude=0.0 인 목록 조회 -> address2로 VWorld 지오코딩 -> 조회된 위경도를 DB에 업데이트하는 함수
def auction_fill_latlng_by_eub_myeon_dong(eub_myeon_dong: str, vworld_api_key: str):
    """
    1) eub_myeon_dong 기준으로 latitude=0.0 인 목록 조회
    2) 각 레코드의 address2 로 VWorld 지오코딩 수행
    3) 조회된 위경도를 DB에 업데이트

    :return:
        {
            "target_count": 대상건수,
            "success_count": 성공건수,
            "fail_count": 실패건수
        }
    """
    target_rows = auction_read_no_latlng_by_eub_myeon_dong(eub_myeon_dong)

    if not target_rows:
        print("[처리종료] 위경도 미처리 대상이 없습니다.")
        return {
            "target_count": 0,
            "success_count": 0,
            "fail_count": 0
        }

    geocoder = VWorldGeocoding(vworld_api_key)

    success_count = 0
    fail_count = 0

    for row in target_rows:
        case_number = row.get("case_number", "")
        address2 = (row.get("address2") or "").strip()

        # 양쪽 괄호 제거 (여러개 있어도 제거)
        address2 = re.sub(r'^\(+|\)+$', '', address2).strip()

        if not address2:
            print(f"[건너뜀] case_number={case_number} / address2 비어있음")
            fail_count += 1
            continue

        # address_type="parcel" (지번), "road" (도로명)
        lat, lng = geocoder.get_lat_lng(address2, address_type="road")

        print(f"[지오코딩결과] case_number={case_number}, address2={address2}, lat={lat}, lng={lng}")

        if float(lat) == 0.0 and float(lng) == 0.0:
            print(f"[실패] case_number={case_number} / 지오코딩 결과 없음")
            fail_count += 1
            continue

        updated = auction_update_latlng_by_case_number(case_number, lat, lng)
        if updated > 0:
            success_count += 1
        else:
            fail_count += 1

    summary = {
        "target_count": len(target_rows),
        "success_count": success_count,
        "fail_count": fail_count
    }

    print(f"[최종요약] {summary}")
    return summary


# 테스트용 메인 실행부
if __name__ == "__main__":
    # -------------------------------
    # 실행 파라미터
    # -------------------------------
    TARGET_EUB_MYEON_DONG = ""

    # -------------------------------
    # 1. 위경도 미처리 대상 조회
    # -------------------------------
    rows = auction_read_no_latlng_by_eub_myeon_dong(TARGET_EUB_MYEON_DONG)

    print("\n[1단계] 조회 결과")
    for idx, row in enumerate(rows, start=1):
        print(
            f"{idx}. case_number={row.get('case_number')}, "
            f"eub_myeon_dong={row.get('eub_myeon_dong')}, "
            f"address2={row.get('address2')}, "
            f"latitude={row.get('latitude')}, longitude={row.get('longitude')}"
        )

    # -------------------------------
    # 2 ~ 3. 지오코딩 + DB 업데이트
    # -------------------------------
    print("\n[2~3단계] 지오코딩 및 DB 업데이트 시작")
    result = auction_fill_latlng_by_eub_myeon_dong(
        eub_myeon_dong=TARGET_EUB_MYEON_DONG,
        vworld_api_key=MAP_API_KEY
    )

    print("\n[최종 결과]")
    print(result)