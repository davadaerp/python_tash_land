# -*- coding: utf-8 -*-
import os
import sqlite3
from typing import List, Dict, Optional, Tuple

from config import PUBLIC_BASE_PATH

DB_PATH = os.path.join(PUBLIC_BASE_PATH, "public_data.db")
TABLE_NAME = "apt_rent"

# ==========================
# apt_rent 테이블 컬럼 정의 (전월세)
# http://apis.data.go.kr/1613000/RTMSDataSvcAptRent
# LAWD_CD(지역코드:5), DEAL_YMD(계약월:6)
# ==========================
RENT_COLUMNS: Tuple[str, ...] = (
    "lawd_cd",
    "sggCd",
    "umdNm",
    "aptNm",
    "jibun",
    "excluUseAr",
    "dealYear",
    "dealMonth",
    "dealDay",
    "deposit",               # 보증금
    "monthlyRent",           # 월세
    "floor",
    "buildYear",
    "contractTerm",
    "contractType",
    "useRRRight",
    "roadnm",               # 도로명
    "roadnmsggcd",
    "roadnmcd",             # 도로명코드
    "roadnmseq",            # 도로명일련번호코드
    "roadnmbcd",            # 도로명지상지하코드
    "roadnmbonbun",
    "roadnmbubun",
    "aptSeq",               # 단지 일련번호
    "preDeposit",
    "preMonthlyRent",
    "lat",
    "lon"
)

def get_conn(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

def init_rent_db(db_path: str = DB_PATH) -> None:
    """
    public_data.db에 apt_rent 테이블 생성.
    아파트 전월세 실거래 데이터 저장용.
    모든 필드는 TEXT로 저장.
    """
    ddl = f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            lawd_cd          TEXT,
            sggCd            TEXT,
            umdNm            TEXT,
            aptNm            TEXT,
            jibun            TEXT,
            excluUseAr       TEXT,
            dealYear         TEXT,
            dealMonth        TEXT,
            dealDay          TEXT,
            deposit          TEXT,
            monthlyRent      TEXT,
            floor            TEXT,
            buildYear        TEXT,
            contractTerm     TEXT,
            contractType     TEXT,
            useRRRight       TEXT,
            roadnm           TEXT,
            roadnmsggcd      TEXT,
            roadnmcd         TEXT,
            roadnmseq        TEXT,
            roadnmbcd        TEXT,
            roadnmbonbun     TEXT,
            roadnmbubun      TEXT,
            aptSeq           TEXT,
            preDeposit       TEXT,
            preMonthlyRent   TEXT,
            lat              TEXT,
            lon              TEXT
        );
    """

    idx1 = f"""
        CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_lawd_year_month
        ON {TABLE_NAME}(lawd_cd, dealYear, dealMonth);
    """

    idx2 = f"""
        CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_apt
        ON {TABLE_NAME}(umdNm, aptNm);
    """

    conn = get_conn(db_path)
    try:
        conn.execute(ddl)
        conn.execute(idx1)
        conn.execute(idx2)
        conn.commit()
    finally:
        conn.close()


def insert_rent_items(items: List[Dict], lawd_cd: str, db_path: str = DB_PATH) -> int:
    """
    수집한 아파트 전월세 items(list[dict])를 apt_rent 테이블에 INSERT.
    각 item에서 필요한 키가 없으면 빈 문자열로 저장.
    반환: INSERT 시도 행 수
    """
    if not items:
        return 0

    placeholders = ",".join(["?"] * len(RENT_COLUMNS))
    cols_sql = ",".join(RENT_COLUMNS)

    sql = f"""
        INSERT OR IGNORE INTO {TABLE_NAME}
        ({cols_sql})
        VALUES ({placeholders})
    """

    rows = []

    for it in items:
        row = (
            str(lawd_cd or ""),
            str(it.get("sggCd", "") or ""),
            str(it.get("umdNm", "") or ""),
            str(it.get("aptNm", "") or ""),
            str(it.get("jibun", "") or ""),
            str(it.get("excluUseAr", "") or ""),
            str(it.get("dealYear", "") or ""),
            str(it.get("dealMonth", "") or ""),
            str(it.get("dealDay", "") or ""),
            str(it.get("deposit", "") or ""),
            str(it.get("monthlyRent", "") or ""),
            str(it.get("floor", "") or ""),
            str(it.get("buildYear", "") or ""),
            str(it.get("contractTerm", "") or ""),
            str(it.get("contractType", "") or ""),
            str(it.get("useRRRight", "") or ""),
            str(it.get("roadnm", "") or ""),
            str(it.get("roadnmsggcd", "") or ""),
            str(it.get("roadnmcd", "") or ""),
            str(it.get("roadnmseq", "") or ""),
            str(it.get("roadnmbcd", "") or ""),
            str(it.get("roadnmbonbun", "") or ""),
            str(it.get("roadnmbubun", "") or ""),
            str(it.get("aptSeq", "") or ""),
            str(it.get("preDeposit", "") or ""),
            str(it.get("preMonthlyRent", "") or ""),
            str(it.get("lat", "") or ""),
            str(it.get("lon", "") or "")
        )
        rows.append(row)

    conn = get_conn(db_path)
    try:
        conn.executemany(sql, rows)
        conn.commit()
        return len(rows)
    finally:
        conn.close()


def read_rent_db(
    lawd_cd: str,
    umd_nm: str = "",
    apt_nm: str = "",
    dealYear: Optional[str] = None,
    dealMonth: Optional[str] = None,
    db_path: str = DB_PATH
) -> List[Dict]:
    """
    apt_rent 테이블에서 전월세 데이터 조회.
    - lawd_cd 필수
    - umd_nm 선택
    - apt_nm 선택
    - dealYear 선택
    - dealMonth 선택
    """
    query = f"""
        SELECT {', '.join(RENT_COLUMNS)}
        FROM {TABLE_NAME}
        WHERE lawd_cd = ?
    """

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
            results.append({
                col: (r[i] if r[i] is not None else "")
                for i, col in enumerate(RENT_COLUMNS)
            })

        return results
    finally:
        conn.close()


def print_rent_rows(rows: List[Dict]) -> None:
    """
    apt_rent 조회 결과 콘솔 출력.
    핵심 컬럼 위주로 확인용.
    """
    if not rows:
        print("전월세 조회 결과가 없습니다.")
        return

    header = (
        f"{'lawd_cd':<8}"
        f"{'dealYear':<8}"
        f"{'dealMonth':<10}"
        f"{'dealDay':<8}"
        f"{'umdNm':<12}"
        f"{'aptNm':<20}"
        f"{'jibun':<12}"
        f"{'excluUseAr':<12}"
        f"{'floor':<8}"
        f"{'deposit':<12}"
        f"{'monthlyRent':<12}"
        f"{'contractType':<12}"
        f"{'preDeposit':<12}"
        f"{'preMonthlyRent':<12}"
    )

    print(header)
    print("-" * len(header))

    for r in rows:
        print(
            f"{r.get('lawd_cd', ''):<8}"
            f"{r.get('dealYear', ''):<8}"
            f"{r.get('dealMonth', ''):<10}"
            f"{r.get('dealDay', ''):<8}"
            f"{r.get('umdNm', ''):<12}"
            f"{r.get('aptNm', ''):<20}"
            f"{r.get('jibun', ''):<12}"
            f"{r.get('excluUseAr', ''):<12}"
            f"{r.get('floor', ''):<8}"
            f"{r.get('deposit', ''):<12}"
            f"{r.get('monthlyRent', ''):<12}"
            f"{r.get('contractType', ''):<12}"
            f"{r.get('preDeposit', ''):<12}"
            f"{r.get('preMonthlyRent', ''):<12}"
        )

# ==========================
# 전월세(rent) 사용 예시
# ==========================
if __name__ == "__main__":

    print("\n===== [APT RENT TEST START] =====")

    # 1) 테이블 생성
    init_rent_db()

    # 2) 샘플 데이터 (전월세)
    sample_rent_items = [
        {
            "sggCd": "41570",
            "umdNm": "운양동",
            "aptNm": "한강신도시롯데캐슬",
            "jibun": "123-1",
            "excluUseAr": "84.99",

            "dealYear": "2025",
            "dealMonth": "03",
            "dealDay": "15",

            "deposit": "30000",
            "monthlyRent": "100",

            "floor": "10",
            "buildYear": "2018",

            "contractTerm": "2년",
            "contractType": "갱신",
            "useRRRight": "사용",

            "roadnm": "김포한강로",
            "roadnmsggcd": "41570",
            "roadnmcd": "1234567",
            "roadnmseq": "01",
            "roadnmbcd": "0",
            "roadnmbonbun": "123",
            "roadnmbubun": "0",

            "aptSeq": "A12345",

            "preDeposit": "28000",
            "preMonthlyRent": "90",

            "lat": "37.6500",
            "lon": "126.6500"
        },
        {
            "sggCd": "41570",
            "umdNm": "운양동",
            "aptNm": "한강신도시롯데캐슬",
            "jibun": "123-1",
            "excluUseAr": "59.99",

            "dealYear": "2025",
            "dealMonth": "02",
            "dealDay": "10",

            "deposit": "20000",
            "monthlyRent": "80",

            "floor": "5",
            "buildYear": "2018",

            "contractTerm": "2년",
            "contractType": "신규",
            "useRRRight": "",

            "roadnm": "김포한강로",
            "roadnmsggcd": "41570",
            "roadnmcd": "1234567",
            "roadnmseq": "01",
            "roadnmbcd": "0",
            "roadnmbonbun": "123",
            "roadnmbubun": "0",

            "aptSeq": "A12345",

            "preDeposit": "",
            "preMonthlyRent": "",

            "lat": "37.6500",
            "lon": "126.6500"
        }
    ]

    # 3) INSERT
    inserted_count = insert_rent_items(sample_rent_items, lawd_cd="41570")
    print(f"[INSERT RENT] 입력 건수: {inserted_count}")

    # 4) READ (조건 조회)
    rent_rows = read_rent_db(
        lawd_cd="41570",
        umd_nm="운양동",
        apt_nm="한강신도시롯데캐슬",
        dealYear="2025"
    )

    print("\n[READ RENT RESULT]")
    print_rent_rows(rent_rows)

    # 5) 수익률 계산 예시 (핵심)
    print("\n[수익률 계산 예시]")
    for r in rent_rows:
        deposit = int(r.get("deposit", "0") or "0")
        monthly = int(r.get("monthlyRent", "0") or "0")

        # 월세 환산가 (기본 200배)
        rent_price = deposit + (monthly * 200)

        print(f"{r.get('aptNm')} | 환산가: {rent_price:,} 만원")

    print("\n===== [APT RENT TEST END] =====")