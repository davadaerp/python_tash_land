# 법정동코드 생성 및 변환 유틸리티
# -*- coding: utf-8 -*-
import os
import sqlite3
from typing import Optional, Dict, List, Iterable, Tuple

from config import CRAWLING_BASE_PATH

DB_PATH = os.path.join(CRAWLING_BASE_PATH, "crawling_data.db")
TABLE_NAME = "crawl_lawd_codes"

# ==========================
# 공용: DB 커넥션
# ==========================
def get_conn(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


# ==========================
# 1) 검색할 법정동코드 저장 테이블 초기화
# ==========================
def init_crawl_lawd_codes_db(db_path: str = DB_PATH) -> None:
    """
    crawl_lawd_codes 테이블 초기화
    - id: INTEGER PRIMARY KEY AUTOINCREMENT
    - lawd_cd + trade_type 복합 인덱스 생성
    """
    ddl = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        lawd_cd    TEXT NOT NULL,
        lawd_name  TEXT NOT NULL,
        trade_type TEXT DEFAULT 'SG'  -- 거래유형 (APT: 아파트, VILLA: 빌라, SG: 상가)
    );
    """

    index_sql = f"""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_{TABLE_NAME}_lawd_trade
    ON {TABLE_NAME} (lawd_cd, trade_type);
    """

    conn = get_conn(db_path)
    try:
        cur = conn.cursor()
        cur.execute(ddl)
        cur.execute(index_sql)
        conn.commit()
        print(f"✅ {TABLE_NAME} 테이블과 복합 인덱스가 정상 생성되었습니다.")
    finally:
        conn.close()

# ==========================
# 2) 단건/대량 입력(UPSERT) 함수
# ==========================
def insert_crawl_lawd_code(
    lawd_cd: str,
    lawd_name: str,
    trade_type: str = "SG",
    db_path: str = DB_PATH
) -> int:
    """
    단건 입력/업데이트(UPSERT)
    - lawd_cd가 존재하면 lawd_name, trade_type 업데이트
    - 존재하지 않으면 INSERT
    반환: 변경된 행 수(rowcount)
    """
    sql = f"""
    INSERT INTO {TABLE_NAME} (lawd_cd, lawd_name, trade_type)
    VALUES (?, ?, ?)
    ON CONFLICT(lawd_cd, trade_type) DO UPDATE SET
        lawd_name = excluded.lawd_name;
    """
    conn = get_conn(db_path)
    try:
        cur = conn.cursor()
        cur.execute(sql, (lawd_cd, lawd_name, trade_type))
        conn.commit()
        print(f"🟢 UPSERT: {lawd_cd} / {lawd_name} / {trade_type}")
        return cur.rowcount
    finally:
        conn.close()


def bulk_insert_crawl_lawd_codes(
    rows: Iterable[Tuple[str, str, str]],
    db_path: str = DB_PATH
) -> int:
    """
    대량 입력/업데이트(UPSERT)
    rows: (lawd_cd, lawd_name, trade_type) 튜플 반복자
    반환: 처리 건수
    """
    sql = f"""
    INSERT INTO {TABLE_NAME} (lawd_cd, lawd_name, trade_type)
    VALUES (?, ?, ?)
    ON CONFLICT(lawd_cd, trade_type) DO UPDATE SET
        lawd_name = excluded.lawd_name;
    """
    conn = get_conn(db_path)
    try:
        cur = conn.cursor()
        cur.executemany(sql, rows)
        conn.commit()
        count = cur.rowcount if cur.rowcount is not None else 0
        print(f"🟢 BULK UPSERT 처리: {count}건")
        return count
    finally:
        conn.close()

# ==========================
# 3) 조회
# ==========================
def search_crawl_lawd_codes(
    db_path: str = DB_PATH,
    lawd_cd: Optional[str] = None,
    lawd_name: Optional[str] = None,
    trade_type: Optional[str] = 'SG'
) -> Optional[List[Dict[str, str]]]:
    """
    crawl_lawd_codes에서 조건(lawd_cd, lawd_name, trade_type)에 맞는 레코드를 조회.
    반환: [{"lawd_cd": "...", "lawd_name": "...", "trade_type": "..."}] 리스트
    조건이 없으면 전체 조회.
    """
    conn = get_conn(db_path)
    try:
        sql = f"SELECT id, lawd_cd, lawd_name, trade_type FROM {TABLE_NAME}"
        params = []
        conditions = []

        if lawd_cd:
            conditions.append("lawd_cd = ?")
            params.append(str(lawd_cd))
        if lawd_name:
            conditions.append("lawd_name LIKE ?")
            params.append(f"%{lawd_name}%")
        if trade_type:
            conditions.append("trade_type = ?")
            params.append(str(trade_type))

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY trade_type, lawd_cd;"

        cur = conn.execute(sql, params)
        rows = cur.fetchall()

        if not rows:
            print("⚠️ 검색 결과가 없습니다.")
            return None

        results = [{"id": r[0], "lawd_cd": r[1], "lawd_name": r[2], "trade_type": r[3]} for r in rows]

        print(f"\n=== 검색 결과 ({len(results)}건) ===")
        for row in results:
            print(f"{row['id']}  | {row['lawd_cd']}  | {row['lawd_name']}  |  {row['trade_type']}")

        return results
    finally:
        conn.close()

# ==========================
# 3) 단건 조회 (lawd_cd + trade_type)
def get_crawl_lawd_code_by_cd_type(
    lawd_cd: str,
    trade_type: str,
    db_path: str = DB_PATH
) -> Optional[Dict[str, str]]:
    """lawd_cd + trade_type로 단건 조회. 없으면 None"""
    conn = get_conn(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            f"SELECT id, lawd_cd, lawd_name, trade_type FROM {TABLE_NAME} "
            "WHERE lawd_cd = ? AND trade_type = ? LIMIT 1;",
            (lawd_cd, trade_type)
        )
        row = cur.fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "lawd_cd": row[1],
            "lawd_name": row[2],
            "trade_type": row[3],
        }
    finally:
        conn.close()

# ==========================
# 4) 삭제 / 초기화 기능
# ==========================
def delete_crawl_lawd_code_by_cd(lawd_cd: str, db_path: str = DB_PATH) -> int:
    """법정동코드(lawd_cd)로 단건 삭제. 반환: 삭제 행 수"""
    conn = get_conn(db_path)
    try:
        cur = conn.cursor()
        cur.execute(f"DELETE FROM {TABLE_NAME} WHERE lawd_cd = ?;", (lawd_cd,))
        conn.commit()
        print(f"🗑️ DELETE by code: {lawd_cd} → {cur.rowcount}건")
        return cur.rowcount
    finally:
        conn.close()

# ==========================
# 4) 삭제 / 초기화 기능 (id 기준)
# ==========================
def delete_crawl_lawd_code_by_id(record_id: int, db_path: str = DB_PATH) -> int:
    """id로 단건 삭제. 반환: 삭제 행 수"""
    conn = get_conn(db_path)
    try:
        cur = conn.cursor()
        cur.execute(f"DELETE FROM {TABLE_NAME} WHERE id = ?;", (int(record_id),))
        conn.commit()
        print(f"🗑️ DELETE by id: {record_id} → {cur.rowcount}건")
        return cur.rowcount
    finally:
        conn.close()

def delete_crawl_lawd_codes(
    db_path: str = DB_PATH,
    lawd_cd: Optional[str] = None,
    lawd_name: Optional[str] = None,
    trade_type: Optional[str] = None
) -> int:
    """
    조건 삭제(다건). 하나도 조건이 없으면 안전을 위해 삭제하지 않음.
    반환: 삭제 행 수
    """
    if not any([lawd_cd, lawd_name, trade_type]):
        print("⛔ 최소 한 가지 조건(lawd_cd, lawd_name, trade_type)이 필요합니다. 전체삭제 방지.")
        return 0

    conn = get_conn(db_path)
    try:
        sql = f"DELETE FROM {TABLE_NAME}"
        params = []
        conditions = []

        if lawd_cd:
            conditions.append("lawd_cd = ?")
            params.append(str(lawd_cd))
        if lawd_name:
            conditions.append("lawd_name LIKE ?")
            params.append(f"%{lawd_name}%")
        if trade_type:
            conditions.append("trade_type = ?")
            params.append(str(trade_type))

        sql += " WHERE " + " AND ".join(conditions)

        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        print(f"🗑️ 조건 삭제: {cur.rowcount}건")
        return cur.rowcount
    finally:
        conn.close()


def clear_crawl_lawd_codes(db_path: str = DB_PATH) -> int:
    """테이블의 모든 데이터(TRUNCATE 유사) 삭제. 반환: 삭제 행 수"""
    conn = get_conn(db_path)
    try:
        cur = conn.cursor()
        cur.execute(f"DELETE FROM {TABLE_NAME};")
        conn.commit()
        print(f"🧹 CLEAR: {TABLE_NAME} 모든 행 삭제({cur.rowcount}건)")
        return cur.rowcount
    finally:
        conn.close()


def drop_crawl_lawd_codes_table(db_path: str = DB_PATH) -> None:
    """테이블 자체를 완전히 삭제(DROP TABLE)."""
    conn = get_conn(db_path)
    try:
        conn.execute(f"DROP TABLE IF EXISTS {TABLE_NAME}")
        conn.commit()
        print(f"[DROP] {TABLE_NAME} 테이블이 삭제되었습니다.")
    finally:
        conn.close()


# ==========================
# 사용 예시
# ==========================
if __name__ == "__main__":
    # 초기화
    init_crawl_lawd_codes_db()

    # sample_data = {
    #     "운양동": "4157010300",
    #     "장기동": "4157010400",
    #     "구래동": "4157010500",
    # }

    # 단건 UPSERT
    insert_crawl_lawd_code("4157010300", "경기도 김포시 운양동", "APT")

    # 대량 UPSERT
    bulk_insert_crawl_lawd_codes([
        ("4157010400", "경기도 김포시 장기동", "APT"),
        ("4157010500", "경기도 김포시 구래동", "APT"),
    ])

    # # 조회 예시
    # search_crawl_lawd_codes(trade_type="SG")
    #
    # # 조건 삭제(예: 상가만 삭제)
    # delete_crawl_lawd_codes(trade_type="SG")
    #
    # # 단건 삭제
    # delete_crawl_lawd_code_by_cd("4113510900")
    #
    # # 데이터만 전체 삭제
    # clear_crawl_lawd_codes()
    #
    # # 테이블 삭제
    # drop_crawl_lawd_codes_table()
