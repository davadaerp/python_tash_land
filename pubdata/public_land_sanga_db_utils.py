# -*- coding: utf-8 -*-
import os
import sqlite3
from typing import List, Dict, Optional, Tuple

from config import PUBLIC_BASE_PATH

DB_PATH = os.path.join(PUBLIC_BASE_PATH, "public_data.db")
TABLE_NAME = "sanga"

# sanga 테이블 컬럼 정의 (모두 TEXT)
SANGA_COLUMNS: Tuple[str, ...] = (
    "lawd_cd",             # 요청에 사용한 법정동 코드(별도 저장)
    "dealYear",
    "dealMonth",
    "dealDay",
    "buildYear",
    "buildingAr",
    "floor",
    "buildingType",
    "buildingUse",
    "buyerGbn",
    "dealAmount",
    "estateAgentSggNm",
    "jibun",
    "landUse",
    "plottageAr",
    "sggCd",
    "sggNm",
    "umdNm",
    "lat",
    "lon",
)

def get_conn(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

def init_sanga_db(db_path: str = DB_PATH) -> None:
    """
    public_data.db에 sanga 테이블 생성 (모든 필드 TEXT).
    lawd_cd, dealYear, dealMonth, dealDay, jibun, buildingAr로 간이 유니크 제약(중복 방지).
    필요 없으면 UNIQUE 구문 제거해도 됨.
    """
    ddl = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        lawd_cd            TEXT,
        dealYear           TEXT,
        dealMonth          TEXT,
        dealDay            TEXT,
        buildYear          TEXT,
        buildingAr         TEXT,
        floor              TEXT,
        buildingType       TEXT,
        buildingUse        TEXT,
        buyerGbn           TEXT,
        dealAmount         TEXT,
        estateAgentSggNm   TEXT,
        jibun              TEXT,
        landUse            TEXT,
        plottageAr         TEXT,
        sggCd              TEXT,
        sggNm              TEXT,
        umdNm              TEXT,
        lat                TEXT,
        lon                TEXT
    );
    """
    idx1 = f"CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_lawd_year_month ON {TABLE_NAME}(lawd_cd, dealYear, dealMonth);"
    # idx2 = f"CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_sgg_umd ON {TABLE_NAME}(sggNm, umdNm);"

    conn = get_conn(db_path)
    try:
        conn.execute(ddl)
        conn.execute(idx1)
        # conn.execute(idx2)
        conn.commit()
    finally:
        conn.close()

def insert_sanga_items(items: List[Dict], lawd_cd: str, db_path: str = DB_PATH) -> int:
    """
    수집한 items(list[dict])을 sanga 테이블에 INSERT.
    각 item에서 필요한 키가 없으면 빈 문자열로 저장.
    반환: 실제로 insert(또는 ignore)된 행 수
    """
    init_sanga_db(db_path)

    #
    if not items:
        return 0

    placeholders = ",".join(["?"] * len(SANGA_COLUMNS))
    cols_sql = ",".join(SANGA_COLUMNS)
    sql = f"INSERT OR IGNORE INTO {TABLE_NAME} ({cols_sql}) VALUES ({placeholders})"

    rows = []
    for it in items:
        row = (
            str(lawd_cd or ""),
            str(it.get("dealYear", "") or ""),
            str(it.get("dealMonth", "") or ""),
            str(it.get("dealDay", "") or ""),
            str(it.get("buildYear", "") or ""),
            str(it.get("buildingAr", "") or ""),
            str(it.get("floor", "") or ""),
            str(it.get("buildingType", "") or ""),
            str(it.get("buildingUse", "") or ""),
            str(it.get("buyerGbn", "") or ""),
            str(it.get("dealAmount", "") or ""),
            str(it.get("estateAgentSggNm", "") or ""),
            str(it.get("jibun", "") or ""),
            str(it.get("landUse", "") or ""),
            str(it.get("plottageAr", "") or ""),
            str(it.get("sggCd", "") or ""),
            str(it.get("sggNm", "") or ""),
            str(it.get("umdNm", "") or ""),
            str(it.get("lat", "") or ""),
            str(it.get("lon", "") or ""),
        )
        rows.append(row)

    conn = get_conn(db_path)
    try:
        cur = conn.executemany(sql, rows)
        conn.commit()
        # sqlite3.Cursor.rowcount는 executemany 시 -1일 수 있으므로, 실제 삽입 수는 변화 감지 대신 len으로 반환
        return len(rows)
    finally:
        conn.close()


def read_sanga_db(lawd_cd: str, umd_nm: str, dealYear: Optional[str] = None, dealMonth: Optional[str] = None,
               db_path: str = DB_PATH) -> List[Dict]:
    """
    sanga 테이블에서 lawd_cd, dealYear, dealMonth 조건으로 조회.
    - dealYear, dealMonth는 선택적(None이면 미필터)
    - 반환: list[dict]
    """
    #
    base = f"SELECT {', '.join(SANGA_COLUMNS)} FROM {TABLE_NAME} WHERE lawd_cd = ?"
    params: List[str] = [str(lawd_cd)]
    if umd_nm is not None:
        base += " AND umdNm = ?"
        params.append(str(umd_nm))

    if dealYear is not None:
        base += " AND dealYear = ?"
        params.append(str(dealYear))
    if dealMonth is not None:
        base += " AND dealMonth = ?"
        params.append(str(dealMonth))
    base += " ORDER BY dealYear, dealMonth, dealDay"

    conn = get_conn(db_path)
    try:
        cur = conn.execute(base, params)
        rows = cur.fetchall()
        results = []
        for r in rows:
            results.append({col: (r[i] if r[i] is not None else "") for i, col in enumerate(SANGA_COLUMNS)})
        return results
    finally:
        conn.close()

def print_rows(rows: List[Dict]) -> None:
    """간단한 표 형태로 화면 출력(핵심 컬럼 위주)."""
    if not rows:
        print("조회 결과가 없습니다.")
        return
    header = (
        f"{'lawd_cd':<8}{'dealYear':<8}{'dealMonth':<10}{'dealDay':<8}"
        f"{'sggNm':<12}{'umdNm':<12}{'jibun':<12}{'dealAmount':<12}"
        f"{'lat':<12}{'lon':<12}"
    )
    print(header)
    print("-" * len(header))
    for r in rows:
        print(
            f"{r.get('lawd_cd',''):<8}"
            f"{r.get('dealYear',''):<8}"
            f"{r.get('dealMonth',''):<10}"
            f"{r.get('dealDay',''):<8}"
            f"{r.get('sggNm',''):<12}"
            f"{r.get('umdNm',''):<12}"
            f"{r.get('jibun',''):<12}"
            f"{r.get('dealAmount',''):<12}"
            f"{r.get('lat',''):<12}"
            f"{r.get('lon',''):<12}"
        )

# ==========================
# 사용 예시
# ==========================
if __name__ == "__main__":
    # 1) DB 초기화(테이블 생성)
    init_sanga_db()

    # 2) (예시) 크롤링/수집 코드에서 만든 items를 DB에 저장
    #    ※ 아래 items 예시는 구조 참고용입니다. 실제로는 수집 루틴에서 받은 items 리스트를 그대로 넣으세요.
    sample_items = [
        {
            "dealYear": "2025", "dealMonth": "07", "dealDay": "30",
            "buildYear": "2007", "buildingAr": "60.38", "floor": "1", "buildingType": "집합",
            "buildingUse": "제2종근린생활", "buyerGbn": "개인", "dealAmount": "40,000",
            "estateAgentSggNm": "경기 용인시 수지구", "jibun": "24", "landUse": "일반상업",
            "plottageAr": "", "sggCd": "11110", "sggNm": "종로구", "umdNm": "종로1가",
            "lat": "37.5729", "lon": "126.9793"
        },
        # ... 추가 행들
    ]
    affected = insert_sanga_items(sample_items, lawd_cd="11110")
    print(f"INSERT 시도 행수: {affected}")

    # 3) READ: lawd_cd만, 혹은 dealYear, dealMonth까지 조건
    res1 = read_sanga_db(lawd_cd="11110", umd_nm="종로1가")
    print("\n[READ] lawd_cd=11110 전체")
    print_rows(res1)

    # res2 = read_sanga_db(lawd_cd="11110", dealYear="2025", dealMonth="07")
    # print("\n[READ] lawd_cd=11110, dealYear=2025, dealMonth=07")
    # print_rows(res2)
