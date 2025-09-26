import os
import json
import requests
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# population_db 모듈에서 CRUD 불러오기
from pubdata.public_population_db_utils import (
    create_population_table,
    population_read_db,
    population_insert_record,
)

session = requests.Session()

# ===== 3) 스키마(표시/정렬 편의를 위한 로컬 리스트) =====
cols_order = [
    "statsYm", "admmCd", "ctpvNm", "sggNm", "dongNm", "tong", "ban",
    "totNmprCnt", "maleNmprCnt", "femlNmprCnt",
    "male0AgeNmprCnt","male10AgeNmprCnt","male20AgeNmprCnt","male30AgeNmprCnt","male40AgeNmprCnt",
    "male50AgeNmprCnt","male60AgeNmprCnt","male70AgeNmprCnt","male80AgeNmprCnt","male90AgeNmprCnt","male100AgeNmprCnt",
    "feml0AgeNmprCnt","feml10AgeNmprCnt","feml20AgeNmprCnt","feml30AgeNmprCnt","feml40AgeNmprCnt",
    "feml50AgeNmprCnt","feml60AgeNmprCnt","feml70AgeNmprCnt","feml80AgeNmprCnt","feml90AgeNmprCnt","feml100AgeNmprCnt",
    "stdgNm", "stdgCd", "liNm",
]

int_cols = [
    "totNmprCnt", "maleNmprCnt", "femlNmprCnt",
    "male0AgeNmprCnt","male10AgeNmprCnt","male20AgeNmprCnt","male30AgeNmprCnt",
    "male40AgeNmprCnt","male50AgeNmprCnt","male60AgeNmprCnt","male70AgeNmprCnt",
    "male80AgeNmprCnt","male90AgeNmprCnt","male100AgeNmprCnt",
    "feml0AgeNmprCnt","feml10AgeNmprCnt","feml20AgeNmprCnt","feml30AgeNmprCnt",
    "feml40AgeNmprCnt","feml50AgeNmprCnt","feml60AgeNmprCnt","feml70AgeNmprCnt",
    "feml80AgeNmprCnt","feml90AgeNmprCnt","feml100AgeNmprCnt",
]

def get_ci(d: dict, key: str):
    if not isinstance(d, dict):
        return None
    kl = key.lower()
    for k, v in d.items():
        if k.lower() == kl:
            return v
    return None

def extract_items(payload):
    """Response/response, body 유무, items/item 다양한 케이스 모두 대응"""
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []

    node = payload
    resp = get_ci(node, "response")
    if isinstance(resp, dict):
        node = resp
    body = get_ci(node, "body")
    if isinstance(body, dict):
        node = body
    items = get_ci(node, "items")
    if items is None:
        items = get_ci(payload, "items")
    if items is None:
        return []
    if isinstance(items, dict):
        itm = get_ci(items, "item")
        if itm is not None:
            items = itm
    if isinstance(items, list):
        return items
    if isinstance(items, dict):
        return [items]
    return []

def to_int_safe(v):
    if v is None or v == "":
        return 0
    try:
        return int(str(v).replace(",", ""))
    except Exception:
        return 0

def normalize_item(item: dict):
    """표시와 DB insert에 쓰기 좋은 형태로 정규화"""
    fixed = dict(item) if isinstance(item, dict) else {}
    for k in int_cols:
        if k in fixed:
            fixed[k] = to_int_safe(fixed[k])
    for k in ["statsYm","admmCd","ctpvNm","sggNm","dongNm","tong","ban","stdgNm","stdgCd","liNm"]:
        fixed[k] = "" if fixed.get(k) is None else str(fixed.get(k))
    ordered = {}
    for k in cols_order:
        if k in fixed:
            ordered[k] = fixed[k]
    for k, v in fixed.items():
        if k not in ordered:
            ordered[k] = v
    return ordered

# ====================== 함수화된 부분 시작 ======================

def build_population_api_request(
    service_key: str,
    stdg_cd: str,
    srch_fr_ym: str,
    srch_to_ym: str,
    lv: str,
    reg_se_cd: str = "1",
    num_of_rows: str = "1000",
    page_no: str = "1",
    user_agent: str = "Mozilla/5.0 (population-fetch/1.0)"
):
    """
    API URL/params/headers를 파라미터로 구성하여 반환
    """
    url = "http://apis.data.go.kr/1741000/stdgSexdAgePpltn/selectStdgSexdAgePpltn"
    params = {
        "serviceKey": service_key,
        "stdgCd": stdg_cd,
        "srchFrYm": srch_fr_ym,
        "srchToYm": srch_to_ym,
        "lv": lv,
        "regSeCd": reg_se_cd,
        "type": "JSON",
        "numOfRows": num_of_rows,
        "pageNo": page_no,
    }
    headers = {"User-Agent": user_agent}
    return url, params, headers

def query_db_by_month(stats_ym: str, sggNm: str, limit: int = 999999):
    """
    DB에서 해당 통계월 자료 조회. 테이블 없으면 생성.
    """
    create_population_table()
    return population_read_db(statsYm=stats_ym, sggNm=sggNm, limit=limit)

def fetch_and_store_from_api(
    session: requests.Session,
    service_key: str,
    stdg_cd: str,
    srch_fr_ym: str,
    srch_to_ym: str,
    lv: str,
    reg_se_cd: str = "1",
    num_of_rows: str = "1000",
    page_no: str = "1",
    timeout: int = 20,
    verify_ssl: bool = False
):
    """
    API 호출 → items 정규화 → DB 적재 → 적재한 목록 반환
    """
    url, params, headers = build_population_api_request(
        service_key, stdg_cd, srch_fr_ym, srch_to_ym, lv,
        reg_se_cd=reg_se_cd, num_of_rows=num_of_rows, page_no=page_no
    )
    resp = session.get(url, params=params, headers=headers, timeout=timeout, verify=verify_ssl)
    resp.raise_for_status()
    data = resp.json()

    items = extract_items(data)
    if not items:
        return []

    normalized = [normalize_item(it) for it in items]
    for rec in normalized:
        population_insert_record(rec)
    return normalized

def get_population_rows(
    stdg_cd: str,
    sgg_nm: str,
    srch_fr_ym: str,
    srch_to_ym: str,
    lv: str,
    *,
    prefer_db: bool = True
):
    SERVICE_KEY = "B2BtWbuZVFz/EJoLsrDa6corOwSR4SsGwjBKzK2WJQ3JVwRMIUoXOGY3BHXrxZq78nP+ECsW5wB4TEwbgxS2PA=="
    """
    1) DB에서 srch_fr_ym 기준으로 조회 (prefer_db=True일 때)
    2) 없으면 API 호출하여 적재 후 반환
    반환: (rows_for_display, rows_source: 'DB' | 'API')
    """
    if prefer_db:
        db_rows = query_db_by_month(srch_fr_ym, sgg_nm, limit=999999)
        if db_rows:
            return db_rows, "DB"

    api_rows = fetch_and_store_from_api(
        session=session,
        service_key=SERVICE_KEY,
        stdg_cd=stdg_cd,
        srch_fr_ym=srch_fr_ym,
        srch_to_ym=srch_to_ym,
        lv=lv
    )
    return api_rows, "API" if api_rows else "API"

# ====================== 함수화된 부분 끝 ======================

def prev_month_yyyymm(base: str | datetime | None = None) -> str:
    """
    base가 None이면 현재일 기준.
    base가 str이면 'YYYYMMDD' 또는 'YYYY-MM-DD' 지원.
    base가 datetime이면 그 날짜 기준.
    반환은 전월 'YYYYMM' 문자열.
    """
    if base is None:
        dt = datetime.now()
    elif isinstance(base, datetime):
        dt = base
    elif isinstance(base, str):
        s = base.strip()
        if len(s) == 8 and s.isdigit():          # 'YYYYMMDD'
            dt = datetime(int(s[0:4]), int(s[4:6]), int(s[6:8]))
        elif len(s) == 10 and s[4] == '-' and s[7] == '-':  # 'YYYY-MM-DD'
            dt = datetime.strptime(s, "%Y-%m-%d")
        else:
            raise ValueError("base 문자열은 'YYYYMMDD' 또는 'YYYY-MM-DD' 형식이어야 합니다.")
    else:
        raise TypeError("base는 None, str, datetime 중 하나여야 합니다.")

    y, m = dt.year, dt.month
    if m == 1:
        y -= 1
        m = 12
    else:
        m -= 1
    return f"{y}{m:02d}"


if __name__ == "__main__":
    # ===== 파라미터 변수 (예시) =====
    STDG_CD     = "4311000000"  # 예: 청주시(4311000000)
    sgg_nm      = "청주시"  # 시군구명 (선택, 빈 문자열이면 전체)
    SRCH_FR_YM  = prev_month_yyyymm()
    SRCH_TO_YM  = prev_month_yyyymm()
    LV          = "3"           # 1:광역시, 2:시군구, 3:읍면동

    # ===== 실행부 =====
    rows_for_display, rows_source = get_population_rows(
        stdg_cd=STDG_CD,
        sgg_nm=sgg_nm,
        srch_fr_ym=SRCH_FR_YM,
        srch_to_ym=SRCH_TO_YM,
        lv=LV,
        prefer_db=True
    )

    # 출력
    display_rows = len(rows_for_display)
    if rows_for_display:
        print(f"\n=== Normalized items (all {display_rows}) — source: {rows_source} ===")
        print(json.dumps(rows_for_display[:2], ensure_ascii=False, indent=2))  # 미리보기 2건
        print(f"\n총 {display_rows}건 출력 (source: {rows_source})")
    else:
        print("\n(items 배열 또는 DB 목록이 비어 있습니다.)")
