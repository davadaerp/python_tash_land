import os
import sqlite3
from config import JUMPO_BASE_PATH

# ─── 공통 변수 ────────────────────────────────────
DB_FILENAME  = os.path.join(JUMPO_BASE_PATH, "jumpo_data.db")
TABLE_NAME   = "jumpo_data"
INFO_TABLE_NAME = "jumpo_data_info_list"

# ─── 테이블 생성 ───────────────────────────────────
def jumpo_create_table():
    """
    jumpo_data 테이블을 생성합니다.
    item_no를 PRIMARY KEY로 지정합니다.
    """
    conn = sqlite3.connect(DB_FILENAME)
    cur = conn.cursor()
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            item_no   TEXT PRIMARY KEY,   -- 매물번호
            section   TEXT,               -- section
            id        TEXT,               -- id
            region    TEXT,               -- 지역
            upjong    TEXT,               -- 업종
            page      INTEGER             -- 페이지
        )
    """)
    conn.commit()
    conn.close()

# ─── 데이터 저장 (종합) ─────────────────────────────
def jumpo_save_to_sqlite(data):
    """
    record 리스트를 받아,
    중복(article_no) 체크 후 신규만 삽입합니다.
    """
    if not data:
        print("저장할 데이터가 없습니다.")
        return

    jumpo_create_table()

    for entry in data:
        jumpo_insert_single(entry)

    print(f"SQLite ({DB_FILENAME})에 {len(data)}건 처리 완료.")

# ─── 단일 레코드 삽입 ───────────────────────────────
def jumpo_insert_single(entry):
    """
    하나의 record를 jumpo_data 테이블에 삽입
    """
    conn = sqlite3.connect(DB_FILENAME)
    cur = conn.cursor()
    sql = f"""
        INSERT INTO {TABLE_NAME} (
            item_no, section, id, region, upjong, page
        ) VALUES (?, ?, ?, ?, ?, ?)
    """
    params = (
        entry["item_no"],
        entry["section"],
        entry["id"],
        entry["region"],
        entry["upjong"],
        entry["page"]
    )
    try:
        cur.execute(sql, params)
        conn.commit()
        print(f"삽입 완료: {entry['item_no']}")
    except Exception as e:
        print(f"삽입 오류 ({entry['item_no']}): {e}")
    finally:
        conn.close()

# ─── 테이블 삭제 ───────────────────────────────────
def jumpo_drop_table():
    """
    jumpo_data 테이블 드롭
    """
    conn = sqlite3.connect(DB_FILENAME)
    cur = conn.cursor()
    cur.execute(f"DROP TABLE IF EXISTS {TABLE_NAME}")
    conn.commit()
    conn.close()
    print(f"테이블 '{TABLE_NAME}' 삭제 완료.")

# ─── 전체 조회 (필터링) ─────────────────────────────
def jumpo_read_db(section="", region="", upjong="", page=None):
    """
    필터 조건에 맞춰 최대 3,000건 조회
    """
    conn = sqlite3.connect(DB_FILENAME)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    sql = f"SELECT * FROM {TABLE_NAME} WHERE 1=1"
    params = []
    if section:
        sql += " AND section = ?";    params.append(section)
    if region:
        sql += " AND region LIKE ?";   params.append(f"%{region}%")
    if upjong:
        sql += " AND upjong LIKE ?";   params.append(f"%{upjong}%")
    if page is not None:
        sql += " AND page = ?";        params.append(page)
    sql += " ORDER BY item_no DESC LIMIT 3000"
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

#=======================================================
# ─── info_list 관련 테이블 구성및 내용 ──────────────────────
# ─── info_list 테이블 생성 ────────────────────────────────
def jumpo_create_info_list_table():
    """
    jumpo_data_info_list 테이블을 생성합니다.
    item_no를 PRIMARY KEY로 지정합니다.
    """
    conn = sqlite3.connect(DB_FILENAME)
    cur = conn.cursor()
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {INFO_TABLE_NAME} (
            item_no            TEXT PRIMARY KEY,
            id                 TEXT,
            section            TEXT,
            업종                TEXT,
            도로명주소           TEXT,
            지번주소             TEXT,
            건축물종류           TEXT,
            해당층수             TEXT,
            대지면적             TEXT,
            전용면적             TEXT,
            공급면적             TEXT,
            건축물주용도         TEXT,
            건축물총층수         TEXT,
            총주차대수           INTEGER,
            사용승인일           TEXT,
            권리금               REAL,
            가맹비용             REAL,
            보증금               REAL,
            월세                REAL,
            관리비              REAL,
            창업비용             REAL,
            월매출               REAL,
            입점비용             REAL,
            마진율               REAL,
            월인건비             REAL,
            매출이익             REAL,
            공과비용             REAL,
            경비합계             REAL,
            기타비용             REAL,
            월수익               REAL,
            월수익률             REAL,
            손익분기점           REAL,
            권리금회수기간        TEXT
        )
    """)
    conn.commit()
    conn.close()

# ─── info_list 단일 조회 ─────────────────────────────────
def jumpo_select_info_list_single(item_no):
    """
    jumpo_data_info_list 에서 item_no 한 건 조회
    """
    conn = sqlite3.connect(DB_FILENAME)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {INFO_TABLE_NAME} WHERE item_no=?", (item_no,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

# ─── info_list 단일 삽입 ─────────────────────────────────
def jumpo_insert_info_list_single(entry):
    """
    하나의 record를 jumpo_data_info_list 테이블에 삽입
    """
    conn = sqlite3.connect(DB_FILENAME)
    cur = conn.cursor()
    sql = f"""
    INSERT INTO {INFO_TABLE_NAME} (
        item_no, id, section, 업종, 도로명주소, 지번주소, 건축물종류, 해당층수,
        대지면적, 전용면적, 공급면적, 건축물주용도, 건축물총층수, 총주차대수,
        사용승인일, 권리금, 가맹비용, 보증금, 월세, 관리비, 창업비용,
        월매출, 입점비용, 마진율, 월인건비, 매출이익, 공과비용, 경비합계,
        기타비용, 월수익, 월수익률, 손익분기점, 권리금회수기간
    ) VALUES (%s)
    """ % ",".join("?" for _ in range(33))
    params = (
        entry["item_no"], entry["id"], entry["section"], entry["업종"],
        entry["도로명주소"], entry["지번주소"], entry["건축물종류"], entry["해당층수"],
        entry["대지면적"], entry["전용면적"], entry["공급면적"], entry["건축물주용도"],
        entry["건축물총층수"], entry["총주차대수"], entry["사용승인일"],
        entry["권리금"], entry["가맹비용"], entry["보증금"], entry["월세"],
        entry["관리비"], entry["창업비용"], entry["월매출"], entry["입점비용"],
        entry["마진율"], entry["월인건비"], entry["매출이익"], entry["공과비용"],
        entry["경비합계"], entry["기타비용"], entry["월수익"], entry["월수익률"],
        entry["손익분기점"], entry["권리금회수기간"]
    )
    try:
        cur.execute(sql, params)
        conn.commit()
        print(f"Info 삽입 완료: {entry['item_no']}")
    except Exception as e:
        print(f"Info 삽입 오류 ({entry['item_no']}): {e}")
    finally:
        conn.close()

# ─── info_list 일괄 저장 ─────────────────────────────────
def jumpo_save_info_list_to_sqlite(data):
    """
    info_list용 record 리스트를 받아,
    중복(item_no) 체크 후 신규만 삽입합니다.
    """
    if not data:
        print("저장할 info_list 데이터가 없습니다.")
        return

    # 테이블 생성여부 처리
    jumpo_create_info_list_table()

    for entry in data:
        exists = jumpo_select_info_list_single(entry["item_no"])
        if exists is None:
            jumpo_insert_info_list_single(entry)
        else:
            print(f"Info 레코드 {entry['item_no']} 이미 존재, 삽입 스킵.")

    print(f"Info 테이블 ({DB_FILENAME})에 {len(data)}건 처리 완료.")

# ─── info_list 조회 (필터링) ─────────────────────────────
def jumpo_read_info_list_db(section="", upjong="", road_addr="", land_addr=""):
    """
    jumpo_data_info_list 에서 필터 조건에 맞춰 조회합니다.
    """
    conn = sqlite3.connect(DB_FILENAME)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    sql = f"SELECT * FROM {INFO_TABLE_NAME} WHERE 1=1"
    params = []
    if section:
        sql += " AND section = ?";    params.append(section)
    if upjong:
        sql += " AND 업종 LIKE ?";     params.append(f"%{upjong}%")
    if road_addr:
        sql += " AND 도로명주소 LIKE ?"; params.append(f"%{road_addr}%")
    if land_addr:
        sql += " AND 지번주소 LIKE ?";  params.append(f"%{land_addr}%")

    sql += " ORDER BY item_no DESC"
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]
