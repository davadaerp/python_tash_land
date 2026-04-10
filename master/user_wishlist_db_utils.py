import os
import sqlite3
from datetime import datetime
from config import MASTER_DB_PATH

# 공통 변수 설정
DB_FILENAME = os.path.join(MASTER_DB_PATH, "master_data.db")
TABLE_NAME = "user_wishlist"

def create_wishlist_table():
    """
    관심물건 테이블을 생성합니다.

    변경사항:
    - user_id 컬럼 추가
    - PRIMARY KEY를 (user_id, case_number) 복합키로 설정
    - eub_myeon_dong 컬럼 인덱스 생성
    """
    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (TABLE_NAME,)
    )
    table_exists = cursor.fetchone() is not None

    if not table_exists:
        cursor.execute(f"""
            CREATE TABLE {TABLE_NAME} (
                user_id TEXT NOT NULL,
                case_number TEXT NOT NULL,
                category TEXT,
                address1 TEXT,
                address2 TEXT,
                lawd_cd TEXT,
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
                opposability_status TEXT,
                personal_status TEXT DEFAULT 'N',
                expected_price TEXT DEFAULT '0',
                latitude TEXT,
                longitude TEXT,
                tid TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, case_number)
            )
        """)

        cursor.execute(
            f"CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_eub_myeon_dong "
            f"ON {TABLE_NAME} (eub_myeon_dong)"
        )
        cursor.execute(
            f"CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_user_id "
            f"ON {TABLE_NAME} (user_id)"
        )
        cursor.execute(
            f"CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_category "
            f"ON {TABLE_NAME} (category)"
        )

        conn.commit()
        print(f"테이블 '{TABLE_NAME}' 생성 완료. (복합키: user_id + case_number)")
    else:
        print(f"테이블 '{TABLE_NAME}' 이(가) 이미 존재합니다.")

    conn.close()


def wishlist_save_to_sqlite(data):
    """
    주어진 data(list of dict)를 SQLite에 저장합니다.
    각 레코드는 (user_id, case_number) 기준으로 INSERT OR REPLACE 처리됩니다.
    """
    if not data:
        print("저장할 데이터가 없습니다.")
        return

    create_wishlist_table()

    count = 0
    for entry in data:
        wishlist_insert_single(entry)
        count += 1

    print(f"SQLite DB({DB_FILENAME})에 {count} 건의 데이터 처리 완료.")


def wishlist_drop_table():
    """
    관심물건 테이블 삭제
    """
    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()
    cursor.execute(f"DROP TABLE IF EXISTS {TABLE_NAME}")
    conn.commit()
    conn.close()
    print(f"테이블 '{TABLE_NAME}' 삭제 완료.")


def wishlist_insert_single(entry):
    """
    단일 레코드를 삽입하거나 교체합니다.
    복합키: (user_id, case_number)
    """
    user_id = entry.get("user_id")
    case_number = entry.get("case_number")

    if not user_id or not case_number:
        print("단일 레코드 삽입 오류: user_id와 case_number는 필수입니다.")
        return

    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    columns = [
        "user_id",
        "case_number",
        "category",
        "address1",
        "address2",
        "lawd_cd",
        "region",
        "sigungu_code",
        "sigungu_name",
        "eub_myeon_dong",
        "building",
        "floor",
        "building_m2",
        "building_py",
        "land_m2",
        "land_py",
        "appraisal_price",
        "min_price",
        "sale_price",
        "min_percent",
        "sale_percent",
        "pydanga_appraisal",
        "pydanga_min",
        "pydanga_sale",
        "sales_date",
        "dangi_name",
        "extra_info",
        "bid_count",
        "bid_rate",
        "deposit_value",
        "bond_total_amount",
        "bond_max_amount",
        "bond_claim_amount",
        "start_decision_date",
        "sale_decision_date",
        "auction_method",
        "auction_applicant",
        "notice_text",
        "opposability_status",
        "personal_status",
        "expected_price",
        "latitude",
        "longitude",
        "tid",
        "created_at",
        "updated_at",
    ]

    values = [
        entry.get("user_id"),
        entry.get("case_number"),
        entry.get("category"),
        entry.get("address1"),
        entry.get("address2"),
        entry.get("lawd_cd"),
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
        entry.get("opposability_status"),
        entry.get("personal_status", "N"),
        entry.get("expected_price", "0"),
        entry.get("latitude"),
        entry.get("longitude"),
        entry.get("tid"),
        entry.get("created_at", now_str),
        now_str,
    ]

    placeholders = ",".join(["?"] * len(columns))
    column_sql = ", ".join(columns)

    insert_query = f"""
        INSERT OR REPLACE INTO {TABLE_NAME} (
            {column_sql}
        ) VALUES (
            {placeholders}
        )
    """

    try:
        cursor.execute(insert_query, values)
        conn.commit()
        print(f"단일 레코드 삽입 완료: user_id={user_id}, case_number={case_number}")
    except Exception as e:
        print(f"단일 레코드 삽입 오류 (user_id={user_id}, case_number={case_number}): {e}")
    finally:
        conn.close()


def wishlist_update_single(entry):
    """
    (user_id, case_number)를 기준으로 단일 레코드를 수정합니다.
    """
    user_id = entry.get("user_id")
    case_number = entry.get("case_number")

    if not user_id or not case_number:
        print("단일 레코드 수정 오류: user_id와 case_number는 필수입니다.")
        return

    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()

    update_query = f"""
        UPDATE {TABLE_NAME} SET
            category = ?,
            address1 = ?,
            address2 = ?,
            lawd_cd = ?,
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
            opposability_status = ?,
            personal_status = ?,
            expected_price = ?,
            latitude = ?,
            longitude = ?,
            tid = ?,
            updated_at = ?
        WHERE user_id = ? AND case_number = ?
    """

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        cursor.execute(update_query, (
            entry.get("category"),
            entry.get("address1"),
            entry.get("address2"),
            entry.get("lawd_cd"),
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
            entry.get("opposability_status"),
            entry.get("personal_status"),
            entry.get("expected_price"),
            entry.get("latitude"),
            entry.get("longitude"),
            entry.get("tid"),
            now_str,
            user_id,
            case_number
        ))
        conn.commit()

        if cursor.rowcount > 0:
            print(f"단일 레코드 수정 완료: user_id={user_id}, case_number={case_number}")
        else:
            print(f"수정 대상 없음: user_id={user_id}, case_number={case_number}")
    except Exception as e:
        print(f"단일 레코드 수정 오류 (user_id={user_id}, case_number={case_number}): {e}")
    finally:
        conn.close()


def wishlist_delete_single(user_id, case_number):
    """
    (user_id, case_number)에 해당하는 단일 레코드를 삭제합니다.
    """
    if not user_id or not case_number:
        print("단일 레코드 삭제 오류: user_id와 case_number는 필수입니다.")
        return

    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()
    delete_query = f"DELETE FROM {TABLE_NAME} WHERE user_id = ? AND case_number = ?"

    try:
        cursor.execute(delete_query, (user_id, case_number))
        conn.commit()

        if cursor.rowcount > 0:
            print(f"레코드 삭제 완료: user_id={user_id}, case_number={case_number}")
        else:
            print(f"삭제 대상 없음: user_id={user_id}, case_number={case_number}")
    except Exception as e:
        print(f"단일 레코드 삭제 오류: {e}")
    finally:
        conn.close()


def wishlist_delete_by_user_id(user_id):
    """
    특정 user_id의 관심물건 전체 삭제
    """
    if not user_id:
        print("사용자 전체 삭제 오류: user_id는 필수입니다.")
        return

    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()
    delete_query = f"DELETE FROM {TABLE_NAME} WHERE user_id = ?"

    try:
        cursor.execute(delete_query, (user_id,))
        conn.commit()
        print(f"user_id={user_id} 전체 삭제 완료. 삭제건수={cursor.rowcount}")
    except Exception as e:
        print(f"user_id 전체 삭제 오류: {e}")
    finally:
        conn.close()


def wishlist_select_single(user_id, case_number):
    """
    (user_id, case_number)에 해당하는 단일 레코드를 조회하여 dict 형태로 반환합니다.
    """
    if not user_id or not case_number:
        print("단일 레코드 조회 오류: user_id와 case_number는 필수입니다.")
        return None

    conn = sqlite3.connect(DB_FILENAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    select_query = f"""
        SELECT *
        FROM {TABLE_NAME}
        WHERE user_id = ? AND case_number = ?
    """

    try:
        cursor.execute(select_query, (user_id, case_number))
        row = cursor.fetchone()
        if row:
            result = dict(row)
            print(f"단일 레코드 조회 완료: user_id={user_id}, case_number={case_number}")
            return result
        else:
            print(f"해당 레코드가 존재하지 않습니다: user_id={user_id}, case_number={case_number}")
            return None
    except Exception as e:
        print(f"단일 레코드 조회 오류: {e}")
        return None
    finally:
        conn.close()


def wishlist_read_db(
    user_id="",
    lawdCd="",
    region="",
    sggNm="",
    umdNm="",
    categories=None
):
    """
    SQLite DB에서 관심물건 데이터를 읽어옵니다.
    """
    conn = sqlite3.connect(DB_FILENAME)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    query = f"SELECT * FROM {TABLE_NAME} WHERE 1=1"
    params = []

    if user_id:
        query += " AND user_id = ?"
        params.append(user_id)

    if lawdCd:
        query += " AND sigungu_code LIKE ?"
        params.append(f"%{lawdCd}%")

    if region:
        query += " AND region LIKE ?"
        params.append(f"%{region}%")

    if sggNm:
        query += " AND sigungu_name LIKE ?"
        params.append(f"%{sggNm}%")

    if umdNm:
        query += " AND eub_myeon_dong LIKE ?"
        params.append(f"%{umdNm}%")

    if categories:
        placeholders = ",".join("?" for _ in categories)
        query += f" AND category IN ({placeholders})"
        params.extend(categories)

    query += " ORDER BY sales_date DESC, category LIMIT 500"

    cur.execute(query, params)
    rows = cur.fetchall()
    result = [dict(row) for row in rows]
    conn.close()
    return result


def wishlist_exists(user_id, case_number):
    """
    관심물건 존재 여부 확인
    """
    row = wishlist_select_single(user_id, case_number)
    return row is not None


def main():
    """
    샘플 실행 함수
    - 테이블 생성
    - admin 사용자 기준 운양동 샘플 3건 저장
    - 조회 / 수정 / 삭제 테스트
    """
    print("=== 관심물건 샘플 테스트 시작 ===")

    create_wishlist_table()

    sample_data = [
        {
            "user_id": "4399854691",
            "case_number": "APT-UNYANG-001",
            "category": "아파트",
            "address1": "경기도 김포시 운양동",
            "address2": "운양동 한강신도시 아파트",
            "lawd_cd": "4157010300",
            "region": "경기도",
            "sigungu_code": "41570",
            "sigungu_name": "김포시",
            "eub_myeon_dong": "운양동",
            "building": "한강신도시자이",
            "floor": "12/20",
            "building_m2": "84.97",
            "building_py": "25.7",
            "land_m2": "45.21",
            "land_py": "13.67",
            "appraisal_price": 650000000,
            "min_price": 520000000,
            "sale_price": 0,
            "min_percent": "80",
            "sale_percent": "",
            "pydanga_appraisal": "25291828",
            "pydanga_min": "20233463",
            "pydanga_sale": "",
            "sales_date": "2026-04-07",
            "dangi_name": "운양동 아파트 샘플",
            "extra_info": "관리상태 양호",
            "bid_count": "0",
            "bid_rate": "",
            "deposit_value": "0",
            "bond_total_amount": "0",
            "bond_max_amount": "0",
            "bond_claim_amount": "0",
            "start_decision_date": "2026-03-15",
            "sale_decision_date": "",
            "auction_method": "임의경매",
            "auction_applicant": "샘플은행",
            "notice_text": "샘플 비고",
            "opposability_status": "없음",
            "personal_status": "N",
            "expected_price": "540000000",
            "latitude": "37.654321",
            "longitude": "126.683210",
            "tid": "TID-APT-001"
        },
        {
            "user_id": "4399854691",
            "case_number": "VILLA-UNYANG-001",
            "category": "빌라",
            "address1": "경기도 김포시 운양동",
            "address2": "운양동 다세대주택",
            "lawd_cd": "4157010300",
            "region": "경기도",
            "sigungu_code": "41570",
            "sigungu_name": "김포시",
            "eub_myeon_dong": "운양동",
            "building": "운양하이빌",
            "floor": "3/4",
            "building_m2": "59.82",
            "building_py": "18.1",
            "land_m2": "31.10",
            "land_py": "9.40",
            "appraisal_price": 310000000,
            "min_price": 248000000,
            "sale_price": 0,
            "min_percent": "80",
            "sale_percent": "",
            "pydanga_appraisal": "17127071",
            "pydanga_min": "13701657",
            "pydanga_sale": "",
            "sales_date": "2026-04-06",
            "dangi_name": "운양동 빌라 샘플",
            "extra_info": "전세 수요 확인 필요",
            "bid_count": "1",
            "bid_rate": "82",
            "deposit_value": "30000000",
            "bond_total_amount": "120000000",
            "bond_max_amount": "150000000",
            "bond_claim_amount": "110000000",
            "start_decision_date": "2026-02-20",
            "sale_decision_date": "",
            "auction_method": "강제경매",
            "auction_applicant": "샘플캐피탈",
            "notice_text": "임차인 점유 가능성 검토",
            "opposability_status": "확인필요",
            "personal_status": "Y",
            "expected_price": "255000000",
            "latitude": "37.653210",
            "longitude": "126.684100",
            "tid": "TID-VILLA-001"
        },
        {
            "user_id": "4399854691",
            "case_number": "COMM-UNYANG-001",
            "category": "상가",
            "address1": "경기도 김포시 운양동",
            "address2": "운양동 근린상가",
            "lawd_cd": "4157010300",
            "region": "경기도",
            "sigungu_code": "41570",
            "sigungu_name": "김포시",
            "eub_myeon_dong": "운양동",
            "building": "운양프라자",
            "floor": "1/8",
            "building_m2": "48.50",
            "building_py": "14.7",
            "land_m2": "12.00",
            "land_py": "3.63",
            "appraisal_price": 420000000,
            "min_price": 336000000,
            "sale_price": 0,
            "min_percent": "80",
            "sale_percent": "",
            "pydanga_appraisal": "28571428",
            "pydanga_min": "22857142",
            "pydanga_sale": "",
            "sales_date": "2026-04-05",
            "dangi_name": "운양동 상가 샘플",
            "extra_info": "유동인구 양호",
            "bid_count": "2",
            "bid_rate": "88",
            "deposit_value": "50000000",
            "bond_total_amount": "200000000",
            "bond_max_amount": "250000000",
            "bond_claim_amount": "180000000",
            "start_decision_date": "2026-01-18",
            "sale_decision_date": "",
            "auction_method": "임의경매",
            "auction_applicant": "샘플저축은행",
            "notice_text": "상가임대차 확인 필요",
            "opposability_status": "있음",
            "personal_status": "N",
            "expected_price": "350000000",
            "latitude": "37.652980",
            "longitude": "126.685340",
            "tid": "TID-COMM-001"
        }
    ]

    print("\n--- 샘플 데이터 저장 ---")
    wishlist_save_to_sqlite(sample_data)

    print("\n--- admin 전체 조회 ---")
    rows = wishlist_read_db(user_id="admin", umdNm="운양동")
    for row in rows:
        print(row)

    # print("\n--- 단건 조회 ---")
    # one_row = wishlist_select_single("admin", "APT-UNYANG-001")
    # print(one_row)
    #
    # print("\n--- 단건 수정 ---")
    # update_entry = {
    #     "user_id": "4399854691",
    #     "case_number": "APT-UNYANG-001",
    #     "category": "아파트",
    #     "address1": "경기도 김포시 운양동",
    #     "address2": "운양동 한강신도시 아파트 수정",
    #     "lawd_cd": "4157010300",
    #     "region": "경기도",
    #     "sigungu_code": "41570",
    #     "sigungu_name": "김포시",
    #     "eub_myeon_dong": "운양동",
    #     "building": "한강신도시자이",
    #     "floor": "15/20",
    #     "building_m2": "84.97",
    #     "building_py": "25.7",
    #     "land_m2": "45.21",
    #     "land_py": "13.67",
    #     "appraisal_price": 660000000,
    #     "min_price": 528000000,
    #     "sale_price": 0,
    #     "min_percent": "80",
    #     "sale_percent": "",
    #     "pydanga_appraisal": "25680933",
    #     "pydanga_min": "20544746",
    #     "pydanga_sale": "",
    #     "sales_date": "2026-04-07",
    #     "dangi_name": "운양동 아파트 샘플 수정",
    #     "extra_info": "수정 테스트",
    #     "bid_count": "1",
    #     "bid_rate": "85",
    #     "deposit_value": "0",
    #     "bond_total_amount": "0",
    #     "bond_max_amount": "0",
    #     "bond_claim_amount": "0",
    #     "start_decision_date": "2026-03-15",
    #     "sale_decision_date": "",
    #     "auction_method": "임의경매",
    #     "auction_applicant": "샘플은행",
    #     "notice_text": "수정된 비고",
    #     "opposability_status": "없음",
    #     "personal_status": "Y",
    #     "expected_price": "550000000",
    #     "latitude": "37.654321",
    #     "longitude": "126.683210",
    #     "tid": "TID-APT-001"
    # }
    # wishlist_update_single(update_entry)
    #
    # print("\n--- 수정 후 단건 조회 ---")
    # one_row_after = wishlist_select_single("admin", "APT-UNYANG-001")
    # print(one_row_after)
    #
    # print("\n--- 단건 삭제 테스트 ---")
    # wishlist_delete_single("admin", "COMM-UNYANG-001")
    #
    # print("\n--- 삭제 후 admin 전체 조회 ---")
    # rows_after_delete = wishlist_read_db(user_id="admin", umdNm="운양동")
    # for row in rows_after_delete:
    #     print(row)

    print("\n=== 관심물건 샘플 테스트 종료 ===")


if __name__ == "__main__":
    main()