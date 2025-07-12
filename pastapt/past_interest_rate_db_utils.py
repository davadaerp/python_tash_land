# 한국은행 기준금리 데이터를 SQLite DB에 저장하고 관리하는 유틸리티
import os
import sqlite3
from config import PAST_APT_BASE_PATH

# 기본 경로와 DB 파일 설정
DB_FILENAME = os.path.join(PAST_APT_BASE_PATH, "past_apt_data.db")
TABLE_NAME = "base_interest_rate"

# 테이블 생성 함수
def create_interest_rate_table():
    conn = sqlite3.connect(DB_FILENAME)
    cur = conn.cursor()

    # id, 연도, 날짜(YYYY-MM-DD), 금리, 비고 컬럼 생성
    cur.execute(f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        year INTEGER NOT NULL,
        date TEXT NOT NULL,
        rate REAL NOT NULL,
        etc TEXT
    )
    """)

    conn.commit()
    conn.close()

# 테이블 삭제 함수
def drop_interest_rate_table():
    conn = sqlite3.connect(DB_FILENAME)
    cur = conn.cursor()

    cur.execute(f"DROP TABLE IF EXISTS {TABLE_NAME}")
    conn.commit()
    conn.close()
    print(f"⚠️ 테이블 `{TABLE_NAME}` 삭제 완료")

# 데이터 삽입 함수
def insert_interest_rate_record(year, date, rate, etc=""):
    conn = sqlite3.connect(DB_FILENAME)
    cur = conn.cursor()

    # date 매개변수는 'MM월 DD일' 형식으로 들어오므로 YYYY-MM-DD로 변환
    month, day = date.split('월 ')
    day = day.replace('일', '')
    formatted_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"

    cur.execute(f"""
    INSERT INTO {TABLE_NAME} (year, date, rate, etc)
    VALUES (?, ?, ?, ?)
    """, (year, formatted_date, rate, etc))

    conn.commit()
    conn.close()

# 전체 조회 함수
def fetch_all_interest_rate_data():
    conn = sqlite3.connect(DB_FILENAME)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(f"""
    SELECT 
        id, 
        year, 
        date,
        rate,
        etc
    FROM {TABLE_NAME}
    ORDER BY date DESC
    """)

    rows = cur.fetchall()
    conn.close()

    return [dict(row) for row in rows]

# 가장최근금리 가져오기
def fetch_latest_interest_rate():
    conn = sqlite3.connect(DB_FILENAME)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(f"""
    SELECT 
        id, 
        year, 
        date,
        rate,
        etc
    FROM {TABLE_NAME}
    ORDER BY date DESC
    LIMIT 1
    """)

    row = cur.fetchone()
    conn.close()

    # # 결과를 년월일,금리 이렇게 리턴해줘
    # if row:
    #     row = dict(row)
    #     row['date'] = row['date'].replace('-', '')
    #     row['rate'] = f"{row['rate']}%"

    return dict(row) if row else None

# HTML 데이터를 파싱하여 DB에 삽입하는 함수
def import_html_data_to_db():
    drop_interest_rate_table()
    create_interest_rate_table()

    html_data = [
        {"year": 2025, "date": "07월 10일", "rate": 2.50},
        {"year": 2025, "date": "05월 29일", "rate": 2.50},
        {"year": 2025, "date": "02월 25일", "rate": 2.75},
        {"year": 2024, "date": "11월 28일", "rate": 3.00},
        {"year": 2024, "date": "10월 11일", "rate": 3.25},
        {"year": 2023, "date": "01월 13일", "rate": 3.50},
        {"year": 2022, "date": "11월 24일", "rate": 3.25},
        {"year": 2022, "date": "10월 12일", "rate": 3.00},
        {"year": 2022, "date": "08월 25일", "rate": 2.50},
        {"year": 2022, "date": "07월 13일", "rate": 2.25},
        {"year": 2022, "date": "05월 26일", "rate": 1.75},
        {"year": 2022, "date": "04월 14일", "rate": 1.50},
        {"year": 2022, "date": "01월 14일", "rate": 1.25},
        {"year": 2021, "date": "11월 25일", "rate": 1.00},
        {"year": 2021, "date": "08월 26일", "rate": 0.75},
        {"year": 2020, "date": "05월 28일", "rate": 0.50},
        {"year": 2020, "date": "03월 17일", "rate": 0.75},
        {"year": 2019, "date": "10월 16일", "rate": 1.25},
        {"year": 2019, "date": "07월 18일", "rate": 1.50},
        {"year": 2018, "date": "11월 30일", "rate": 1.75},
        {"year": 2017, "date": "11월 30일", "rate": 1.50},
        {"year": 2016, "date": "06월 09일", "rate": 1.25},
        {"year": 2015, "date": "06월 11일", "rate": 1.50},
        {"year": 2015, "date": "03월 12일", "rate": 1.75},
        {"year": 2014, "date": "10월 15일", "rate": 2.00},
        {"year": 2014, "date": "08월 14일", "rate": 2.25},
        {"year": 2013, "date": "05월 09일", "rate": 2.50},
        {"year": 2012, "date": "10월 11일", "rate": 2.75},
        {"year": 2012, "date": "07월 12일", "rate": 3.00},
        {"year": 2011, "date": "06월 10일", "rate": 3.25},
        {"year": 2011, "date": "03월 10일", "rate": 3.00},
        {"year": 2011, "date": "01월 13일", "rate": 2.75},
        {"year": 2010, "date": "11월 16일", "rate": 2.50},
        {"year": 2010, "date": "07월 09일", "rate": 2.25},
        {"year": 2009, "date": "02월 12일", "rate": 2.00},
        {"year": 2009, "date": "01월 09일", "rate": 2.50},
        {"year": 2008, "date": "12월 11일", "rate": 3.00},
        {"year": 2008, "date": "11월 07일", "rate": 4.00},
        {"year": 2008, "date": "10월 27일", "rate": 4.25},
        {"year": 2008, "date": "10월 09일", "rate": 5.00},
        {"year": 2008, "date": "08월 07일", "rate": 5.25},
        {"year": 2007, "date": "08월 09일", "rate": 5.00},
        {"year": 2007, "date": "07월 12일", "rate": 4.75},
        {"year": 2006, "date": "08월 10일", "rate": 4.50},
        {"year": 2006, "date": "06월 08일", "rate": 4.25},
        {"year": 2006, "date": "02월 09일", "rate": 4.00},
        {"year": 2005, "date": "12월 08일", "rate": 3.75},
        {"year": 2005, "date": "10월 11일", "rate": 3.50},
        {"year": 2004, "date": "11월 11일", "rate": 3.25},
        {"year": 2004, "date": "08월 12일", "rate": 3.50},
        {"year": 2003, "date": "07월 10일", "rate": 3.75},
        {"year": 2003, "date": "05월 13일", "rate": 4.00},
        {"year": 2002, "date": "05월 07일", "rate": 4.25},
        {"year": 2001, "date": "09월 19일", "rate": 4.00},
        {"year": 2001, "date": "08월 09일", "rate": 4.50},
        {"year": 2001, "date": "07월 05일", "rate": 4.75},
        {"year": 2001, "date": "02월 08일", "rate": 5.00},
        {"year": 2000, "date": "10월 05일", "rate": 5.25},
        {"year": 2000, "date": "02월 10일", "rate": 5.00},
        {"year": 1999, "date": "05월 06일", "rate": 4.75}
    ]

    for data in html_data:
        insert_interest_rate_record(data["year"], data["date"], data["rate"], "한국은행 기준금리")


# 예시 실행
if __name__ == "__main__":
    # HTML 데이터를 DB에 삽입
    import_html_data_to_db()

    # 삽입된 데이터 출력
    for row in fetch_all_interest_rate_data():
        print(f"{row['date']} - 기준금리: {row['rate']}%  ({row['etc']})")