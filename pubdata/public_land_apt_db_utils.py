# -*- coding: utf-8 -*-
import os
import sqlite3
from typing import List, Dict, Optional, Tuple

from config import PUBLIC_BASE_PATH

DB_PATH = os.path.join(PUBLIC_BASE_PATH, "public_data.db")
TABLE_NAME = "apt"

# apt 테이블 컬럼 정의 (모두 TEXT)
APT_COLUMNS: Tuple[str, ...] = (
    "lawd_cd",             # 요청에 사용한 법정동 코드(별도 저장)
    "dealYear",
    "dealMonth",
    "dealDay",
    "buildYear",
    "excluUseAr",   # 전용면적
    "landAr",       # 대지면적
    "floor",
    "slerGbn",           # 매도자(개인/법인/공공기관/기타)
    "buyerGbn",         # 매수자구분(개인/법인/공공기관/기타)
    "dealAmount",
    "estateAgentSggNm", # 중개사소재지
    "dealingGbn",       # 거래유형(중개및 직거래여부)
    "rgstDate",         # 등기일자
    "sggCd",
    "sggNm",
    "umdNm",
    "aptNm",      # 단지명(현진빌라B동 등)
    "jibun",
    "aptDong",    # 아파트 동명(101동)
    "lat",
    "lon"
)

def get_conn(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

def init_apt_db(db_path: str = DB_PATH) -> None:
    """
    public_data.db에 sanga 테이블 생성 (모든 필드 TEXT).
    lawd_cd, dealYear, dealMonth, dealDay, jibun, buildingAr로 간이 유니크 제약(중복 방지).
    필요 없으면 UNIQUE 구문 제거해도 됨.
    """
    #
    ddl = f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            lawd_cd            TEXT,
            dealYear           TEXT,
            dealMonth          TEXT,
            dealDay            TEXT,
            buildYear          TEXT,
            excluUseAr         TEXT,        
            landAr             TEXT,        
            floor              TEXT,
            slerGbn             TEXT,
            buyerGbn           TEXT,
            dealAmount         TEXT,
            estateAgentSggNm   TEXT,
            dealingGbn         TEXT,
            rgstDate           TEXT,
            sggCd              TEXT,
            sggNm              TEXT,
            umdNm              TEXT,
            aptNm              TEXT,
            jibun              TEXT,
            aptDong            TEXT,
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

def insert_apt_items(items: List[Dict], lawd_cd: str, db_path: str = DB_PATH) -> int:
    """
    수집한 items(list[dict])을 sanga 테이블에 INSERT.
    각 item에서 필요한 키가 없으면 빈 문자열로 저장.
    반환: 실제로 insert(또는 ignore)된 행 수
    """
    #init_apt_db(db_path)

    #
    if not items:
        return 0

    placeholders = ",".join(["?"] * len(APT_COLUMNS))
    cols_sql = ",".join(APT_COLUMNS)
    sql = f"INSERT OR IGNORE INTO {TABLE_NAME} ({cols_sql}) VALUES ({placeholders})"

    rows = []
    for it in items:
        row = (
            str(lawd_cd or ""),
            str(it.get("dealYear", "") or ""),
            str(it.get("dealMonth", "") or ""),
            str(it.get("dealDay", "") or ""),
            str(it.get("buildYear", "") or ""),
            str(it.get("excluUseAr", "") or ""),
            str(it.get("landAr", "") or ""),
            str(it.get("floor", "") or ""),
            str(it.get("slerGbn", "") or ""),
            str(it.get("buyerGbn", "") or ""),
            str(it.get("dealAmount", "") or ""),
            str(it.get("estateAgentSggNm", "") or ""),
            str(it.get("dealingGbn", "") or ""),
            str(it.get("rgstDate", "") or ""),
            str(it.get("sggCd", "") or ""),
            str(it.get("sggNm", "") or ""),
            str(it.get("umdNm", "") or ""),
            str(it.get("aptNm", "") or ""),
            str(it.get("jibun", "") or ""),
            str(it.get("aptDong", "") or ""),
            str(it.get("lat", "") or ""),
            str(it.get("lon", "") or "")
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


def read_apt_db(lawd_cd: str, umd_nm: str, apt_nm: str, dealYear: Optional[str] = None, dealMonth: Optional[str] = None,
               db_path: str = DB_PATH) -> List[Dict]:
    """
    sanga 테이블에서 lawd_cd, dealYear, dealMonth 조건으로 조회.
    - dealYear, dealMonth는 선택적(None이면 미필터)
    - 반환: list[dict]
    """
    #
    query = f"SELECT {', '.join(APT_COLUMNS)} FROM {TABLE_NAME} WHERE lawd_cd = ?"
    params: List[str] = [str(lawd_cd)]
    if umd_nm:
        query += " AND umdNm LIKE ?"
        params.append(f"%{umd_nm.strip()}%")
    if apt_nm:
        query += " AND aptNm = ?"
        params.append(str(apt_nm))

    if dealYear is not None:
        query += " AND dealYear = ?"
        params.append(str(dealYear))
    if dealMonth is not None:
        query += " AND dealMonth = ?"
        params.append(str(dealMonth))
    query += " ORDER BY dealYear, dealMonth, dealDay"

    conn = get_conn(db_path)
    try:
        cur = conn.execute(query, params)
        rows = cur.fetchall()
        results = []
        for r in rows:
            results.append({col: (r[i] if r[i] is not None else "") for i, col in enumerate(APT_COLUMNS)})
        return results
    finally:
        conn.close()

def print_rows(rows: List[Dict]) -> None:
    """간단한 표 형태로 화면 출력(핵심 컬럼 위주)."""
    if not rows:
        print("조회 결과가 없습니다.")
        return
    header = (
        f"{'lawd_cd':<8}{'dealYear':<8}{'dealMonth':<10}{'dealDay':<8}{'excluUseAr':<12} "
        f"{'sggNm':<12}{'umdNm':<12}{'aptNm':<20}{'jibun':<12}{'aptDong':<20}{'dealAmount':<12}"
        f"{'lat':<12}{'lon':<12}{'slerGbn':<12}{'buyerGbn':<12}"
    )
    print(header)
    print("-" * len(header))
    for r in rows:
        print(
            f"{r.get('lawd_cd',''):<8}"
            f"{r.get('dealYear',''):<8}"
            f"{r.get('dealMonth',''):<10}"
            f"{r.get('dealDay',''):<8}"
            f"{r.get('excluUseAr',''):<12} "
            f"{r.get('sggNm',''):<12}"
            f"{r.get('umdNm',''):<12}"
            f"{r.get('aptNm',''):<20}"
            f"{r.get('jibun',''):<12}"
            f"{r.get('aptDong',''):<12}"
            f"{r.get('dealAmount',''):<12}"
            f"{r.get('lat',''):<12}"
            f"{r.get('lon',''):<12}"
            f"{r.get('slerGbn',''):<12}"
            f"{r.get('buyerGbn',''):<12}"
        )

# ==========================
# 사용 예시
# ==========================
if __name__ == "__main__":
    # # 1) DB 초기화(테이블 생성)
    # init_apt_db()
    #
    # # 2) (예시) 크롤링/수집 코드에서 만든 items를 DB에 저장
    # #    ※ 아래 items 예시는 구조 참고용입니다. 실제로는 수집 루틴에서 받은 items 리스트를 그대로 넣으세요.
    # sample_items = [
    #     {
    #         "dealYear": "2025", "dealMonth": "07", "dealDay": "30",
    #         "buildYear": "2007", "excluUseAr": "60.38", "landAr": "10.38", "floor": "1",
    #         "slerGbn": "개인", "buyerGbn": "개인", "dealAmount": "40,000",
    #         "estateAgentSggNm": "경기 용인시 수지구", "dealingGbn": "개인", "rgstDate": "2025-09-01",
    #         "sggCd": "11110", "sggNm": "종로구", "umdNm": "종로1가",
    #         "aptNm": "현대아파트", "jibun": "202-3", "aptDong": "101동",
    #         "lat": "37.5729", "lon": "126.9793"
    #     },
    #     # ... 추가 행들
    # ]
    # affected = insert_apt_items(sample_items, lawd_cd="11110")
    # print(f"INSERT 시도 행수: {affected}")

    # 3) READ: lawd_cd만, 혹은 dealYear, dealMonth까지 조건
    res1 = read_apt_db(lawd_cd="41570", umd_nm="운양동", apt_nm="", dealYear="2025", dealMonth="1")
    print("\n[READ] lawd_cd=41570 전체")
    print_rows(res1)
