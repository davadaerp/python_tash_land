import csv
import os
import sqlite3
import pandas as pd
#
from config import CRAWLING_BASE_PATH

# 공통 변수 설정
#DB_FILENAME = "/Users/wfight/IdeaProjects/PythonProject/Auction/sanga/apt_data.db"
DB_FILENAME = os.path.join(CRAWLING_BASE_PATH, "crawling_data.db")
TABLE_NAME = "sanga_data"

def sanga_create_table():
    """
    sanga_data 테이블을 생성합니다.
    article_no를 PRIMARY KEY로 지정하고, umdNm 컬럼에 인덱스를 생성합니다.
    테이블이 이미 존재하면 아무런 메시지도 출력하지 않습니다.
    """
    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            article_no TEXT PRIMARY KEY,
            page INTEGER,
            lawdCd TEXT,
            umdNm TEXT,
            confirm_date_str TEXT,
            article_name TEXT,
            real_estate_type TEXT,
            real_estate_name TEXT,
            trade_type TEXT,
            trade_name TEXT,
            price TEXT,
            hanPrc TEXT,
            rentPrc TEXT,
            area1 TEXT,
            area2 TEXT,
            exclusive_area_pyeong REAL,
            direction TEXT,
            building_name TEXT,
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
            sale_rent_price TEXT,
            fav TEXT
        )
    """)
    # umdNm 컬럼에 인덱스 생성 (eub_myeon_dong이 아닌 상가 데이터에서는 umdNm을 사용)
    cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_lawdCd_umdNm ON {TABLE_NAME}(lawdCd, umdNm)")
    conn.commit()
    conn.close()
    # 테이블이 이미 존재하면 메시지를 출력하지 않음

def sanga_save_to_sqlite(data):
    """
    주어진 data (리스트 내의 dict들)를 SQLite 데이터베이스에 저장합니다.
    멀티 입력의 경우 각 레코드를 sanga_insert_single 함수를 이용하여 처리합니다.
    full_save가 True이면 기존 테이블을 삭제하고 재생성합니다.
    """
    if not data:
        print("저장할 데이터가 없습니다.")
        return

    # 테이블이 없는 경우 생성 (단, 메시지는 출력하지 않음)
    sanga_create_table()

    for entry in data:
        """
          삽입 전에 article_no(고유키)가 이미 존재하는지 확인하여, 존재하지 않을 때만 삽입합니다.
          """
        # 이미 존재하는지 체크
        existing = sanga_select_single(entry.get("article_no"))
        if existing is None:
            sanga_insert_single(entry)
        else:
            # entry["feature_desc"] = str(entry.get("feature_desc")) + " update"
            # sanga_update_single(entry)
            print(f"레코드 {entry.get('article_no')}는 이미 존재합니다. 삽입 건너뜀(update).")

    print(f"SQLite DB({DB_FILENAME})에 {len(data)} 건의 레코드 처리 완료.")

def sanga_drop_table():
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
def sanga_insert_single(entry):
    """
    단일 레코드를 삽입합니다.
    """
    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()
    insert_query = f"""
        INSERT INTO {TABLE_NAME} (
            article_no, page, lawdCd, umdNm, confirm_date_str, article_name, real_estate_type, real_estate_name,
            trade_type, trade_name, price, hanPrc, rentPrc, area1, area2,
            exclusive_area_pyeong, direction, building_name, cfloor, tfloor, realtor_name, company_name,
            article_url, latitude, longitude, tag_list, feature_desc, sale_deposit_price, sale_rent_price
        ) VALUES (?,?,?,?,?,?,?,?,
                  ?,?,?,?,?,?,?,
                  ?,?,?,?,?,?,?,
                  ?,?,?,?,?,?,?)
    """
    try:
        cursor.execute(insert_query, (
            entry.get("article_no"),
            entry.get("page"),
            entry.get("lawdCd"),
            entry.get("umdNm"),
            entry.get("confirm_date_str"),
            entry.get("article_name"),
            entry.get("real_estate_type"),
            entry.get("real_estate_name"),
            entry.get("trade_name"),            # trade_type을 내용(월세/전세/매매)으로 채웜 => 'A1' → "매매", 'B1' → "전세", 'B2' → "월세"
            entry.get("trade_name"),
            entry.get("price"),
            entry.get("hanPrc"),
            entry.get("rentPrc"),
            entry.get("area1"),
            entry.get("area2"),
            entry.get("exclusive_area_pyeong"),
            entry.get("direction"),
            entry.get("building_name"),
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
        print(f"레코드 {entry.get('article_no')} 삽입 완료.")
    except Exception as e:
        print(f"레코드 {entry.get('article_no')} 삽입 오류: {e}")
    finally:
        conn.close()

def sanga_update_single(entry):
    """
    article_no를 기준으로 단일 레코드를 수정합니다.
    entry에는 수정할 값들과 article_no가 포함되어야 합니다.
    """
    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()
    update_query = f"""
        UPDATE {TABLE_NAME} SET
            page = ?,
            lawdCd = ?,
            umdNm = ?,
            confirm_date_str = ?,
            article_name = ?,
            real_estate_type = ?,
            real_estate_name = ?,
            trade_type = ?,
            trade_name = ?,
            price = ?,
            hanPrc = ?,
            rentPrc = ?,
            area1 = ?,
            area2 = ?,
            exclusive_area_pyeong = ?,
            direction = ?,
            building_Name = ?,
            cfloor = ?,
            tfloor = ?,
            realtor_name = ?,
            company_name = ?,
            article_url = ?,
            latitude = ?,
            longitude = ?,
            tag_list = ?,
            feature_desc = ?,
            sale_deposit_price = ?,
            sale_rent_price = ?
        WHERE article_no = ?
    """
    try:
        cursor.execute(update_query, (
            entry.get("page"),
            entry.get("lawdCd"),
            entry.get("umdNm"),
            entry.get("confirm_date_str"),
            entry.get("article_name"),
            entry.get("real_estate_type"),
            entry.get("real_estate_name"),
            entry.get("trade_type"),
            entry.get("trade_name"),
            entry.get("price"),
            entry.get("hanPrc"),
            entry.get("rentPrc"),
            entry.get("area1"),
            entry.get("area2"),
            entry.get("exclusive_area_pyeong"),
            entry.get("direction"),
            entry.get("building_name"),
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
            entry.get("sale_rent_price"),
            entry.get("article_no")
        ))
        conn.commit()
        print(f"레코드 {entry.get('article_no')} 수정 완료.")
    except Exception as e:
        print(f"레코드 {entry.get('article_no')} 수정 오류: {e}")
    finally:
        conn.close()

# 즐겨찾기 저장
def sanga_update_fav(article_no, fav):
    """
    article_no를 기준으로 단일 레코드를 수정합니다.
    entry에는 수정할 값들과 article_no가 포함되어야 합니다.
    """
    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()
    update_query = f"""
        UPDATE {TABLE_NAME} SET fav = ? WHERE article_no = ?
    """
    try:
        cursor.execute(update_query, (fav, article_no))
        conn.commit()
        return {"result": "SUCCESS", "message" : "레코드 {article_no} 즐거찾기 수정 완료."}
    except Exception as e:
        return {"result": "FAIL", "message" : "레코드 {article_no} 즐거찾기 수정 오류: {e}"}
    finally:
        conn.close()


def sanga_delete_single(article_no):
    """
    주어진 article_no에 해당하는 단일 레코드를 삭제합니다.
    """
    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()
    delete_query = f"DELETE FROM {TABLE_NAME} WHERE article_no = ?"
    try:
        cursor.execute(delete_query, (article_no,))
        conn.commit()
        print(f"레코드 {article_no} 삭제 완료.")
    except Exception as e:
        print(f"레코드 {article_no} 삭제 오류: {e}")
    finally:
        conn.close()


def sanga_select_single(article_no):
    """
    주어진 article_no에 해당하는 단일 레코드를 조회하여 dict 형태로 반환합니다.
    """
    conn = sqlite3.connect(DB_FILENAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    select_query = f"SELECT * FROM {TABLE_NAME} WHERE article_no = ?"
    try:
        cursor.execute(select_query, (article_no,))
        row = cursor.fetchone()
        if row:
            result = dict(row)
            print(f"레코드 {article_no} 조회 완료.")
            return result
        else:
            print(f"레코드 {article_no}가 존재하지 않습니다.")
            return None
    except Exception as e:
        print(f"레코드 {article_no} 조회 오류: {e}")
        return None
    finally:
        conn.close()

def sanga_read_db(lawdCd="", umdNm="", trade_type="", sale_year="", category="", dangiName=""):
    """
    SQLite DB에서 데이터를 읽어와 필터 조건에 따라 반환합니다.
    """
    conn = sqlite3.connect(DB_FILENAME)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    query = f"SELECT * FROM {TABLE_NAME} WHERE 1=1"
    params = []
    if lawdCd:
        query += " AND lawdCd=?"
        params.append(lawdCd)
    if umdNm:
        query += " AND umdNm LIKE ?"
        params.append("%" + umdNm + "%")
    if trade_type:
        query += " AND trade_type LIKE ?"
        params.append("%" + trade_type + "%")
    if category:
        query += " AND article_name LIKE ?"
        params.append("%" + category + "%")
    if dangiName:
        query += " AND dangi_name LIKE ?"
        params.append("%" + dangiName + "%")
    query += " ORDER BY confirm_date_str DESC LIMIT 3000"
    cur.execute(query, params)
    rows = cur.fetchall()
    print("조회된 레코드 수:", len(rows))
    data = [dict(row) for row in rows]
    conn.close()
    return data

# 볍정동코드 가져오기
LAW_FILENAME = os.path.join(CRAWLING_BASE_PATH, "법정동코드.txt")
def extract_law_codes(region, sigungu, umdNm):
    law_code = ''
    with open(LAW_FILENAME, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        for row in reader:
            # 각 행이 3개 이상의 필드를 가지고 있는지 확인
            if len(row) < 3:
                continue
            code = row[0].strip()
            location = row[1].strip()
            status = row[2].strip()

            # 상태가 "존재"인지 확인
            if status != "존재":
                continue

            # location 필드를 공백으로 분리하여 지역, 시군구, 읍면동 추출
            tokens = location.split()
            if len(tokens) < 3:
                continue

            file_region = tokens[0]
            # 토큰 개수가 4개 이상이면 시군구는 두 토큰(예: "고양시 덕양구"), 읍면동은 네번째 토큰
            if len(tokens) >= 4:
                file_sigungu = tokens[1] + " " + tokens[2]
                file_umdNm = tokens[3]
            else:
                file_sigungu = tokens[1]
                file_umdNm = tokens[2]

            # 입력된 region, sigungu, umdNm과 모두 일치할 때 해당 법정동 코드를 반환
            if file_region == region and file_sigungu == sigungu and file_umdNm == umdNm:
                law_code = code
                break

    return law_code


#=== WAL/체크포인트 유틸 (append-only) =====================================
import atexit
import signal
from typing import Optional

def get_db_path() -> str:
    """
    이 모듈이 사용하는 DB 경로를 반환합니다.
    우선순위:
      1) 모듈 내 DB_FILENAME 상수
      2) 환경변수 SANGA_DB_PATH
      3) 현재 경로의 'sanga_data.db'
    """
    try:
        return DB_FILENAME  # 상단에 정의되어 있음
    except Exception:
        return os.environ.get("CRAWLING_BASE_PATH", os.path.abspath("./crawling_data.db"))

def sqlite_enable_wal(db_path: Optional[str] = None, synchronous: str = "NORMAL") -> None:
    """
    시작 시 한 번 호출: WAL 모드 활성화 + 동기화 레벨 설정
    - synchronous: "FULL"|"NORMAL"|"OFF" 중 선택
    """
    path = db_path or get_db_path()
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute(f"PRAGMA synchronous={synchronous};")
    print(f"[WAL] journal_mode=WAL, synchronous={synchronous} 적용 → {path}")

def sqlite_checkpoint(db_path: Optional[str] = None, mode: str = "FULL") -> None:
    """
    종료 시 WAL 체크포인트 수행.
    - mode: "PASSIVE"|"FULL"|"RESTART"|"TRUNCATE"
    """
    path = db_path or get_db_path()
    with sqlite3.connect(path) as conn:
        conn.execute(f"PRAGMA wal_checkpoint({mode});")
    print(f"[WAL] checkpoint({mode}) 완료 → {path}")

def _safe_checkpoint(db_path: Optional[str] = None, mode: str = "FULL") -> None:
    try:
        sqlite_checkpoint(db_path, mode)
    except Exception as e:
        print(f"[WAL] checkpoint 실패: {e}")

def install_sqlite_shutdown_hooks(db_path: Optional[str] = None, mode: str = "FULL") -> None:
    """
    atexit 훅과 SIGINT/SIGTERM 핸들러를 등록해
    프로세스 종료 시점에 체크포인트를 보장합니다.
    """
    path = db_path or get_db_path()

    # atexit 훅
    atexit.register(lambda: _safe_checkpoint(path, mode))

    # 신호 처리(가능한 플랫폼에서만)
    def _handler(signum, frame):
        _safe_checkpoint(path, mode)
        try:
            # 기본 핸들러 복구 후 동일 신호 재전달(정상 종료 유도)
            signal.signal(signum, signal.SIG_DFL)
            os.kill(os.getpid(), signum)
        except Exception:
            pass

    for sig in (getattr(signal, "SIGINT", None), getattr(signal, "SIGTERM", None)):
        if sig is None:
            continue
        try:
            signal.signal(sig, _handler)
        except Exception:
            pass

    print(f"[WAL] 종료 훅 설치 완료 (mode={mode}) → {path}")
# === WAL/체크포인트 유틸 끝 ================================================