import os
import sqlite3
from config import PAST_APT_BASE_PATH

# DB 파일 경로 설정
DB_FILENAME = os.path.join(PAST_APT_BASE_PATH, "past_apt_data.db")
TABLE_NAME = "apt_sale_price_index"

def create_apt_sale_price_index_table():
    """
    apt_sale_price_index 테이블 생성
    필드: id, region, address, sale_date(YYYY-MM-DD), sale_index(지수)
    """
    conn = sqlite3.connect(DB_FILENAME)
    cur = conn.cursor()

    cur.execute(f'''
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            region TEXT NOT NULL,
            address TEXT NOT NULL,
            sale_date TEXT NOT NULL,
            sale_index REAL NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

def drop_apt_sale_price_index_table():
    """
    apt_sale_price_index 테이블 삭제
    """
    conn = sqlite3.connect(DB_FILENAME)
    cur = conn.cursor()

    cur.execute(f'''DROP TABLE IF EXISTS {TABLE_NAME}''')
    conn.commit()
    conn.close()
    print(f"⚠️ 테이블 `{TABLE_NAME}` 삭제 완료")

def insert_apt_sale_price_index_record(region: str, address: str, sale_date: str, sale_index: float):
    """
    apt_sale_price_index 테이블에 단일 레코드 삽입
    """
    conn = sqlite3.connect(DB_FILENAME)
    cur = conn.cursor()

    cur.execute(f'''
        INSERT INTO {TABLE_NAME} (region, address, sale_date, sale_index)
        VALUES (?, ?, ?, ?)
    ''', (region, address, sale_date, sale_index))

    conn.commit()
    conn.close()

# 지역을 기준으로 공급물량 목록
def fetch_latest_sale_index_by_address(region: str, address: str):
    """
    주어진 region과 address에 대해 그룹핑 후, 각 그룹에서 최신 sale_date의 매매지수를 조회합니다.
    """
    conn = sqlite3.connect(DB_FILENAME)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    query = f'''
        SELECT t1.region, t1.address, t1.sale_date, t1.sale_index
        FROM {TABLE_NAME} t1
        JOIN (
            SELECT region, address, MAX(sale_date) AS max_date
            FROM {TABLE_NAME}
            WHERE region LIKE ? AND address LIKE ?
            GROUP BY region, address
        ) t2 ON t1.region = t2.region AND t1.address = t2.address AND t1.sale_date = t2.max_date
    '''
    cur.execute(query, (f"%{region}%", f"%{address}%"))
    rows = cur.fetchall()
    conn.close()

    # 결과를 딕셔너리 형태로 변환
    return [dict(row) for row in rows]


# region, address를 조건으로 조회하는 main함수 실행을 추가해줘
if __name__ == '__main__':
    result = fetch_latest_sale_index_by_address(region="서울특별시", address="")
    print(result)