# 년도별 평균근로자소득
import os
import sqlite3
from config import PAST_APT_BASE_PATH

# 기본 경로와 DB 파일 설정
DB_FILENAME = os.path.join(PAST_APT_BASE_PATH, "past_apt_data.db")
TABLE_NAME = "average_annual_income"

# 테이블 생성 함수
def create_income_table():
    conn = sqlite3.connect(DB_FILENAME)
    cur = conn.cursor()

    cur.execute(f'''
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER,
            income INTEGER,     -- 월평균소득 (만원)
            etc TEXT
        )
    ''')

    conn.commit()
    conn.close()

# 데이터 삽입 함수
def insert_income_record(year, income, etc=""):
    conn = sqlite3.connect(DB_FILENAME)
    cur = conn.cursor()

    cur.execute(f'''
        INSERT INTO {TABLE_NAME} (year, income, etc)
        VALUES (?, ?, ?)
    ''', (year, income, etc))

    conn.commit()
    conn.close()

# 전체 조회 함수
def fetch_all_income_data():
    conn = sqlite3.connect(DB_FILENAME)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(f'''
        SELECT 
            id, 
            year, 
            income, 
            CAST(income * 12 / 10000 AS INTEGER) AS year_income,
            etc
        FROM {TABLE_NAME}
        ORDER BY year ASC
    ''')

    rows = cur.fetchall()
    conn.close()

    return [dict(row) for row in rows]

# 예시 실행 (테이블 생성 후 일부 샘플 데이터 삽입)
if __name__ == "__main__":
    # create_income_table()
    # insert_income_record(1999, 2234643, "근로자가구 월소득")
    # insert_income_record(2000, 2388231, "근로자가구 월소득")
    # insert_income_record(2001, 2658217, "근로자가구 월소득")
    # insert_income_record(2002, 2835445, "근로자가구 월소득")
    # insert_income_record(2003, 2930755, "근로자가구 월소득")
    # insert_income_record(2004, 3112474, "근로자가구 월소득")
    # insert_income_record(2005, 3252090, "근로자가구 월소득")
    # insert_income_record(2006, 3444054, "근로자가구 월소득")
    # insert_income_record(2007, 3656201, "근로자가구 월소득")
    # insert_income_record(2008, 3900622, "근로자가구 월소득")
    # insert_income_record(2009, 3853189, "근로자가구 월소득")
    # insert_income_record(2010, 4007671, "근로자가구 월소득")
    # insert_income_record(2011, 4248619, "근로자가구 월소득")
    # insert_income_record(2012, 4492364, "근로자가구 월소득")
    # insert_income_record(2013, 4606216, "근로자가구 월소득")
    # insert_income_record(2014, 4734603, "근로자가구 월소득")
    # insert_income_record(2015, 4980000, "근로자가구 월소득")
    # insert_income_record(2016, 5170000, "근로자가구 월소득")
    # insert_income_record(2017, 5380000, "근로자가구 월소득")
    # insert_income_record(2018, 5600000, "근로자가구 월소득")
    # insert_income_record(2019, 5620081, "근로자가구 소득")
    # insert_income_record(2020, 5794406, "근로자가구 소득")
    # insert_income_record(2021, 6236968, "근로자가구 소득")
    # insert_income_record(2022, 6452108, "근로자가구 소득")
    # insert_income_record(2023, 6804310, "근로자가구 소득")
    # insert_income_record(2024, 7093331, "근로자가구 소득")

    data = fetch_all_income_data()
    for row in data:
        print(row)
