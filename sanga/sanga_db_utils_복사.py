import csv
import sqlite3
import pandas as pd

# 공통 변수 설정
CSV_FILENAME = "sanga_data.csv"
DB_FILENAME = "/sanga/sanga_data.db"
TABLE_NAME = "sanga_data"

def sanga_save_to_csv(data):
    """
    주어진 data (리스트 내의 dict들)를 CSV 파일로 저장합니다.
    """
    if not data:
        print("저장할 데이터가 없습니다.")
        return
    # data에 새 필드가 포함되어 있으므로 자동으로 반영됨
    keys = list(data[0].keys())
    with open(CSV_FILENAME, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)
    print(f"CSV 파일({CSV_FILENAME}) 저장 완료.")


def sanga_save_to_sqlite(data, full_save=True):
    """
    주어진 data (리스트 내의 dict들)를 SQLite DB에 저장합니다.
    """
    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            page INTEGER,
            umdNm TEXT,
            article_no TEXT,
            confirm_date_str TEXT,
            article_name TEXT,
            real_estate_type TEXT,
            article_real_estate_type TEXT,
            trade_type TEXT,
            price TEXT,
            rentPrc TEXT,
            area1 TEXT,
            area2 TEXT,
            exclusive_area_pyeong REAL,
            direction TEXT,
            cfloor TEXT,
            tfloor TEXT,
            realtor_name TEXT,
            company_name TEXT,
            article_url TEXT,
            latitude TEXT,
            longitude TEXT,
            tag_list TEXT,
            feature_desc TEXT,
            sale_deposit_price TEXT,
            sale_rent_price TEXT
        )
    """)

    insert_query = f"""
        INSERT INTO {TABLE_NAME} (
            page, umdNm, article_no, confirm_date_str, article_name, real_estate_type, 
            article_real_estate_type, trade_type, price, rentPrc, area1, area2, 
            exclusive_area_pyeong, direction, cfloor, tfloor, realtor_name, company_name, 
            article_url, latitude, longitude, tag_list, feature_desc, sale_deposit_price, sale_rent_price
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """
    for entry in data:
        cursor.execute(insert_query, (
            entry.get("page"),
            entry.get("umdNm"),
            entry.get("article_no"),
            entry.get("confirm_date_str"),
            entry.get("article_name"),
            entry.get("real_estate_type"),
            entry.get("article_real_estate_type"),
            entry.get("trade_type"),
            entry.get("price"),
            entry.get("rentPrc"),
            entry.get("area1"),
            entry.get("area2"),
            entry.get("exclusive_area_pyeong"),
            entry.get("direction"),
            entry.get("cfloor"),
            entry.get("tfloor"),
            entry.get("realtor_name"),
            entry.get("company_name"),
            entry.get("article_url"),
            entry.get("latitude"),
            entry.get("longitude"),
            entry.get("tag_list"),
            entry.get("feature_desc"),
            entry.get("sale_deposit_price"),
            entry.get("sale_rent_price")
        ))
    conn.commit()
    conn.close()
    print(f"SQLite DB({DB_FILENAME}) 저장 완료.")


def sanga_delete_table():
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

# CSV 파일 읽기 및 필터링 함수
def sanga_read_csv(lawdCd="", umdNm="", trade_type="", sale_year="", sale_month="", category="", dangiName=""):
    df = pd.read_csv(CSV_FILENAME, dtype=str)
    df.fillna("", inplace=True)

    # 필터링 조건 적용
    if umdNm:
        df = df[df['umdNm'].str.contains(umdNm, na=False)]
    if trade_type:
        df = df[df['trade_type'].str.contains(trade_type, na=False)]
    if category:
        df = df[df['article_name'].str.contains(category, na=False)]
    if sale_year:
        df = df[df['confirm_date_str'].str.startswith(sale_year)]
    if sale_month:
        df = df[df['confirm_date_str'].str[5:7] == sale_month]

    return df.to_dict(orient='records')


# SQLite DB 파일 읽기 및 필터링 함수
def sanga_read_db(lawdCd="", umdNm="", trade_type="", sale_year="", sale_month="", category="", dangiName=""):
    conn = sqlite3.connect(DB_FILENAME)
    conn.row_factory = sqlite3.Row  # 각 행을 dict처럼 취급
    cur = conn.cursor()
    query = f"SELECT * FROM {TABLE_NAME} WHERE 1=1"
    params = []
    if umdNm:
        query += " AND umdNm LIKE ?"
        params.append("%" + umdNm + "%")
    if trade_type:
        query += " AND trade_type LIKE ?"
        params.append("%" + trade_type + "%")
    if category:
        query += " AND article_name LIKE ?"
        params.append("%" + category + "%")
    if sale_year:
        query += " AND confirm_date_str LIKE ?"
        params.append(sale_year + "%")
    if sale_month:
        query += " AND SUBSTR(confirm_date_str,6,2) = ?"
        params.append(sale_month)
    if dangiName:
        query += " AND dangi_name LIKE ?"
        params.append("%" + dangiName + "%")

    # confirm_date_str를 기준으로 최근순(내림차순) 정렬하고, 기본 300개 레코드만 반환
    query += " ORDER BY confirm_date_str DESC LIMIT 1000"

    cur.execute(query, params)
    rows = cur.fetchall()
    data = [dict(row) for row in rows]
    conn.close()
    return data