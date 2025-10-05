# 법정동코드 생성 및 변환 유틸리티
# -*- coding: utf-8 -*-
import os
import sqlite3
import csv
from typing import Optional, Dict

from config import PUBLIC_BASE_PATH

DB_PATH = os.path.join(PUBLIC_BASE_PATH, "public_data.db")
TABLE_NAME = "lawd_code"

# ==========================
# 공용: DB 커넥션
# ==========================
def get_conn(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

# ==========================
# 1) 테이블 생성
# ==========================
def init_lawd_db(db_path: str = DB_PATH) -> None:
    """
    lawd_code(lawd_cd TEXT, lawd_name TEXT)
    - lawd_cd를 PRIMARY KEY로 설정(= 인덱스 포함)
    """
    ddl = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        lawd_cd   TEXT PRIMARY KEY,
        lawd_name TEXT NOT NULL
    );
    """
    conn = get_conn(db_path)
    try:
        conn.execute(ddl)
        conn.commit()
    finally:
        conn.close()

# ==========================
# 2) TXT 읽어서 로드(‘존재’만)
# ==========================
def load_lawd_from_txt(txt_path: str, db_path: str = DB_PATH) -> int:
    """
    탭 구분 텍스트(헤더 포함)를 읽어 ‘폐지여부’가 ‘존재’인 행만 INSERT OR REPLACE.
    컬럼: 법정동코드, 법정동명, 폐지여부
    반환: 적재한(INSERT/REPLACE) 행 수
    """
    init_lawd_db(db_path)

    if not os.path.exists(txt_path):
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {txt_path}")

    # UTF-8 BOM 유연 처리
    inserted = 0
    conn = get_conn(db_path)
    try:
        sql = f"INSERT OR REPLACE INTO {TABLE_NAME} (lawd_cd, lawd_name) VALUES (?, ?)"
        with open(txt_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f, delimiter="\t")
            header = next(reader, None)

            # 헤더 유효성(유연 매칭)
            if header is None or len(header) < 3:
                raise ValueError("입력 파일의 헤더가 유효하지 않습니다. (법정동코드, 법정동명, 폐지여부)")

            # 컬럼 인덱스 탐색(한글 헤더 그대로일 때)
            try:
                idx_code = header.index("법정동코드")
                idx_name = header.index("법정동명")
                idx_stat = header.index("폐지여부")
            except ValueError:
                # 예상 헤더명이 아닐 경우, 위치 기반으로도 허용(1,2,3열)
                idx_code, idx_name, idx_stat = 0, 1, 2

            rows = []
            for row in reader:
                if not row or len(row) <= max(idx_code, idx_name, idx_stat):
                    continue
                code = row[idx_code].strip()
                name = row[idx_name].strip()
                stat = row[idx_stat].strip()

                # ‘존재’만 반영
                if stat == "존재" and code and name:
                    rows.append((code, name))

            if rows:
                conn.executemany(sql, rows)
                conn.commit()
                inserted = len(rows)
    finally:
        conn.close()

    return inserted

# ==========================
# 3) lawd_cd로 단건 조회
# ==========================
def get_lawd_by_code(lawd_cd: str, db_path: str = DB_PATH) -> Optional[Dict[str, str]]:
    """
    lawd_cd로 lawd_code 테이블에서 단건 조회.
    반환: {"lawd_cd": "...", "lawd_name": "..."} 또는 None
    """
    if not lawd_cd:
        return None

    conn = get_conn(db_path)
    try:
        sql = f"SELECT lawd_cd, lawd_name FROM {TABLE_NAME} WHERE lawd_cd = ?"
        cur = conn.execute(sql, (str(lawd_cd),))
        row = cur.fetchone()
        if not row:
            return None
        return {"lawd_cd": row[0], "lawd_name": row[1]}
    finally:
        conn.close()

# ==========================
# 4) 삭제 / 초기화 기능 추가
# ==========================
def drop_lawd_table(db_path: str = DB_PATH) -> None:
    """lawd_code 테이블 자체를 완전히 삭제(DROP TABLE)."""
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
    # 1) 테이블 생성
    init_lawd_db()

    # 4) 테이블/데이터 삭제 예시
    # drop_lawd_table()     # 테이블 전체 삭제

    # 2) TXT 로드 (예: /path/to/법정동코드.txt)
    #    헤더: 법정동코드\t법정동명\t폐지여부
    sample_txt = "법정동코드.txt"
    try:
        n = load_lawd_from_txt(sample_txt)
        print(f"[LOAD] 적재 행수: {n}")
    except FileNotFoundError:
        print(f"[SKIP] 파일 없음: {sample_txt}")

    # 3) 코드로 단건 조회
    res = get_lawd_by_code("1111010300")
    print("[READ]", res)
