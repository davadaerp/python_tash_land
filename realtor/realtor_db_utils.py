import os
import csv
import sqlite3

import pandas as pd

# 현재 파일(realtor_db_utils.py)의 상위 디렉토리(/tash)를 sys.path에 추가
# current_dir = os.path.dirname(os.path.abspath(__file__))
# parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
# if parent_dir not in sys.path:
#     sys.path.insert(0, parent_dir)

from config import REALTOR_DB_PATH

# 공통 변수 설정
CSV_FILENAME = "realtor_data.csv"
DB_FILENAME = os.path.join(REALTOR_DB_PATH, "realtor_data.db")
TABLE_NAME = "realtor_data"


def realtor_create_table():
    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            mem_no TEXT,
            title TEXT,
            representative TEXT,
            address1 TEXT,
            address2 TEXT,
            landline_phone TEXT,
            mobile_phone TEXT,
            sel_type TEXT
        )
    """)
    conn.commit()
    conn.close()


def realtor_insert_record(record):
    """
    단일 레코드를 테이블에 삽입합니다.
    mobile_phone 컬럼에 대해 중복 여부를 확인하며,
    중복되지 않을 경우에만 데이터를 삽입합니다.

    파라미터:
        record (dict): {
            "mem_no": str,
            "title": str,
            "representative": str,
            "address1": str,
            "address2": str,
            "landline_phone": str,
            "mobile_phone": str
        }
    """
    # 테이블이 없으면 생성
    realtor_create_table()

    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()

    mobile = record.get("mobile_phone")
    # 동일한 mobile_phone 값이 이미 존재하는지 확인
    cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE mobile_phone = ?", (mobile,))
    count = cursor.fetchone()[0]

    if count == 0:
        insert_query = f"""
            INSERT INTO {TABLE_NAME} (
                mem_no, title, representative, address1, address2, landline_phone, mobile_phone, sel_type
            ) VALUES (?,?,?,?,?,?,?,?)
        """
        cursor.execute(insert_query, (
            record.get("mem_no"),
            record.get("title"),
            record.get("representative"),
            record.get("address1"),
            record.get("address2"),
            record.get("landline_phone"),
            mobile,
            record.get("sel_type")
        ))
        conn.commit()
        print(f"mobile_phone {mobile} 값의 레코드가 성공적으로 삽입되었습니다.")
    else:
        print(f"mobile_phone {mobile} 은(는) 이미 존재합니다. 삽입을 건너뜁니다.")

    conn.close()

# 폰번호 존재하면 update, 없으면 insert
def realtor_insert_or_update_record(record):
    """
    단일 레코드를 테이블에 삽입하거나, mobile_phone 기준으로
    이미 존재하면 업데이트합니다.

    파라미터:
        record (dict): {
            "mem_no": str,
            "title": str,
            "representative": str,
            "address1": str,
            "address2": str,
            "landline_phone": str,
            "mobile_phone": str,
            "sel_type": str
        }
    """
    # 테이블이 없으면 생성
    realtor_create_table()

    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()

    mobile = record.get("mobile_phone")

    # 동일한 mobile_phone 값이 이미 존재하는지 확인
    cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE mobile_phone = ?", (mobile,))
    exists = cursor.fetchone()[0] > 0

    if not exists:
        # INSERT
        insert_sql = f"""
            INSERT INTO {TABLE_NAME} (
                mem_no, title, representative,
                address1, address2, landline_phone,
                mobile_phone, sel_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(insert_sql, (
            record["mem_no"],
            record["title"],
            record["representative"],
            record["address1"],
            record["address2"],
            record["landline_phone"],
            mobile,
            record["sel_type"]
        ))
        print(f"mobile_phone {mobile} 값의 레코드를 새로 삽입했습니다.")
    else:
        # UPDATE
        update_sql = f"""
            UPDATE {TABLE_NAME}
               SET mem_no        = ?,
                   title         = ?,
                   representative= ?,
                   address1      = ?,
                   address2      = ?,
                   landline_phone= ?,
                   sel_type      = ?
             WHERE mobile_phone  = ?
        """
        cursor.execute(update_sql, (
            record["mem_no"],
            record["title"],
            record["representative"],
            record["address1"],
            record["address2"],
            record["landline_phone"],
            record["sel_type"],
            mobile
        ))
        print(f"mobile_phone {mobile} 값의 레코드를 업데이트했습니다.")

    conn.commit()
    conn.close()


def realtor_save_to_sqlite(data_list):
    # 테이블생성 (테이블이 없으면 생성)
    realtor_create_table()

    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()
    insert_query = f"""
        INSERT INTO {TABLE_NAME} (
            mem_no, title, representative, address1, address2, landline_phone, mobile_phone, sel_type
        ) VALUES (?,?,?,?,?,?,?,?)
    """
    # data_list의 각 항목에 대해 mobile_phone 값이 이미 존재하는지 확인 후 저장
    for entry in data_list:
        mobile = entry.get("mobile_phone")
        # 동일한 mobile_phone 값이 이미 존재하는지 조회
        cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE mobile_phone = ?", (mobile,))
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.execute(insert_query, (
                entry.get("mem_no"),
                entry.get("title"),
                entry.get("representative"),
                entry.get("address1"),
                entry.get("address2"),
                entry.get("landline_phone"),
                mobile,
                'realtor'
            ))
        else:
            print(f"mobile_phone {mobile} 는 이미 존재합니다. (건너뜁니다.)")
    conn.commit()
    conn.close()
    print(f"SQLite DB('{DB_FILENAME}')에 데이터가 저장되었습니다.")

def realtor_drop_table():
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


def realtor_read_db(lawdCd="", selType="", searchTitle="", dangiName=""):
    """
    SQLite DB에서 데이터를 읽어옵니다.
    여기서는 실제 테이블에 저장된 컬럼을 기준으로 필터링합니다.
    예를 들어, umdNm은 address1 컬럼, dangiName은 address2 컬럼에서 검색하도록 처리합니다.
    """
    conn = sqlite3.connect(DB_FILENAME)
    conn.row_factory = sqlite3.Row  # 각 행을 dict처럼 사용할 수 있게 함
    cur = conn.cursor()
    query = f"SELECT * FROM {TABLE_NAME} WHERE 1=1"
    params = []
    if selType:
        query += " AND sel_type = ?"
        params.append(f"{selType}")
    if searchTitle:
        query += " AND title LIKE ?"
        params.append(f"%{searchTitle}%")
    if dangiName:
        query += " AND address2 LIKE ?"
        params.append(f"%{dangiName}%")
    query += " LIMIT 130"
    # lawdCd는 사용하지 않는 예시 조건입니다.
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def realtor_save_to_csv(data_list):
    """
    파싱된 데이터 리스트(data_list)를 CSV 파일에 저장합니다.
    파일이 존재하면 append 방식, 없으면 새로 생성하며 헤더를 작성합니다.
    CSV 필드: mem_no, title, representative, address1, address2, landline_phone, mobile_phone
    """
    fieldnames = ["mem_no", "title", "representative", "address1", "address2", "landline_phone", "mobile_phone"]
    mode = "a" if os.path.exists(CSV_FILENAME) and os.path.getsize(CSV_FILENAME) > 0 else "w"
    with open(CSV_FILENAME, mode, newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if mode == "w":
            writer.writeheader()
        for row in data_list:
            writer.writerow(row)
    print(f"CSV 파일 '{CSV_FILENAME}'에 데이터가 저장되었습니다.")

def realtor_read_csv(lawdCd="", umdNm="", dangiName=""):
    df = pd.read_csv(CSV_FILENAME, dtype=str)
    df.fillna("", inplace=True)
    # 예시) umdNm이나 dangiName 필터링 조건을 아래와 같이 적용할 수 있습니다.
    # if umdNm:
    #     df = df[df['address1'].str.contains(umdNm, na=False)]
    # if dangiName:
    #     df = df[df['address2'].str.contains(dangiName, na=False)]
    return df.to_dict(orient='records')



