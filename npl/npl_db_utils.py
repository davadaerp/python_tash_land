import os
from datetime import datetime
import sqlite3
import pandas as pd
#
from config import NPL_DB_PATH

# 공통 변수 설정
DB_FILENAME = os.path.join(NPL_DB_PATH, "npl_data.db")
TABLE_NAME = "npl_data"

def create_npl_table():
    """
    npl_data 테이블을 생성합니다.
    case_number를 PRIMARY KEY로 지정하고, eub_myeon_dong 컬럼에 인덱스를 생성합니다.
    새로운 필드:
        deposit_value: 임차보증금금액
        bond_total_amount: 총채권합계금액
        bond_max_amount: 채권최고액
        bond_claim_amount: 채권청구액
        start_decision_date: 경매개시일자
        auction_method: 경매청구방식
        auction_applicant: 경매신청자
        notice_text: 비고내역(임차권등기/유치권/법정지상권등)
        expected_price: 예상낙찰가  <-- 사람이 입력함
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
                case_number TEXT PRIMARY KEY,
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
                -- 아래부터 새로 추가된 필드들
                bid_count TEXT,
                bid_rate TEXT,                                          
                deposit_value TEXT,
                bond_total_amount TEXT,
                bond_max_amount TEXT,
                bond_claim_amount TEXT,
                start_decision_date TEXT,
                sale_decision_date TEXT,
                auction_method TEXT,
                auction_applicant TEXT,
                notice_text TEXT,
                expected_price TEXT, -- 예상낙찰가 
                latitude TEXT,
                longitude TEXT
            )
        """)
        # 인덱스
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_eub_myeon_dong ON {TABLE_NAME} (eub_myeon_dong)")
        conn.commit()
        print(f"테이블 '{TABLE_NAME}' 생성 완료 (새 필드 포함).")

    conn.close()

def npl_save_to_sqlite(data):
    """
    주어진 data (리스트 내의 dict들)를 SQLite 데이터베이스에 저장하는 함수.
    각 레코드의 case_number를 기준으로 존재 여부를 확인하지 않고 무조건 삽입합니다.
    """
    if not data:
        print("저장할 데이터가 없습니다.")
        return

    create_npl_table()

    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()
    for entry in data:
        npl_insert_single(entry)

    print(f"SQLite DB({DB_FILENAME})에 {len(data)} 건의 데이터 처리 완료.")

def npl_drop_table():
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

def npl_insert_single(entry):
    """
    단일 레코드를 삽입합니다.
    :param entry: dict 형태의 레코드 데이터 (case_number가 반드시 포함되어야 함)
    """
    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()
    insert_query = f"""
        INSERT OR REPLACE INTO {TABLE_NAME} (
            case_number,
            category, address1, address2, region,
            sigungu_code, sigungu_name, eub_myeon_dong,
            building, floor, building_m2, building_py,
            land_m2, land_py, appraisal_price,
            min_price, sale_price, min_percent,
            sale_percent, pydanga_appraisal,
            pydanga_min, pydanga_sale, sales_date,
            dangi_name, extra_info,
            bid_count, bid_rate,
            deposit_value, bond_total_amount,
            bond_max_amount, bond_claim_amount,
            start_decision_date, sale_decision_date, auction_method,
            auction_applicant, notice_text, expected_price,
            latitude, longitude
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """
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
            # 새 필드들:
            entry.get("bid_count"),
            entry.get("bid_rate"),
            entry.get("deposit_value"),
            entry.get("bond_total_amount"),
            entry.get("bond_max_amount"),
            entry.get("bond_claim_amount"),
            entry.get("start_decision_date"),
            entry.get("sale_decision_date"),
            entry.get("auction_method"),
            entry.get("auction_applicant"),
            entry.get("notice_text"),
            entry.get("expected_price"),    # 예상낙찰가
            entry.get("latitude"),
            entry.get("longitude")
        ))
        conn.commit()
        print(f"단일 레코드 삽입 완료: case_number={entry.get('case_number')}")
    except Exception as e:
        print(f"단일 레코드 삽입 오류 (case_number={entry.get('case_number')}):", e)
    finally:
        conn.close()

def npl_update_single(entry):
    """
    case_number를 기준으로 단일 레코드를 수정합니다.
    :param entry: dict 형태의 레코드 데이터 (수정할 값들과 case_number 포함)
    """
    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()
    update_query = f"""
        UPDATE {TABLE_NAME} SET
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
            bid_count = ?,
            bid_rate = ?,
            deposit_value = ?,
            bond_total_amount = ?,
            bond_max_amount = ?,
            bond_claim_amount = ?,
            start_decision_date = ?,
            sale_decision_date = ?,
            auction_method = ?,
            auction_applicant = ?,
            notice_text = ?,
            expected_price = ?,
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
            # 새 필드들:
            entry.get("deposit_value"),
            entry.get("bond_total_amount"),
            entry.get("bond_max_amount"),
            entry.get("bond_claim_amount"),
            entry.get("start_decision_date"),
            entry.get("sale_decision_date"),
            entry.get("auction_method"),
            entry.get("auction_applicant"),
            entry.get("notice_text"),
            entry.get("expected_price"),
            entry.get("latitude"),
            entry.get("longitude"),
            entry.get("case_number")
        ))
        conn.commit()
        print(f"단일 레코드 수정 완료: case_number={entry.get('case_number')}")
    except Exception as e:
        print(f"단일 레코드 수정 오류 (case_number={entry.get('case_number')}):", e)
    finally:
        conn.close()

def npl_delete_single(case_number):
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

def npl_select_single(case_number):
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

def npl_read_db(lawdCd="", umdNm="", year_range="2", categories=None, dangiName=""):
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
    current_date = datetime.today().strftime("%Y-%m-%d")
    if year_range == "1":
        start_date = f"{datetime.today().year}-01-01"
    elif year_range == "2":
        start_date = f"{datetime.today().year - 1}-01-01"
    else:
        start_date = None

    if start_date:
        query += " AND sales_date BETWEEN ? AND ?"
        params.append(start_date)
        params.append(current_date)

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
