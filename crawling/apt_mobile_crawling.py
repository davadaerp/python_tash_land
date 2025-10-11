# -*- coding: utf-8 -*-
"""
네이버 모바일 부동산(https://m.land.naver.com) 상가(SG) 매물 크롤링 예제
- 단계(1)~(6)을 함수로 분리
- 키워드 배열로 다건 검색 가능
- 랜덤 User-Agent/쿠키/지연(차단 회피), 간단 재시도(backoff)
- 목록 출력 및 CSV 저장 옵션

※ 주의: 사이트 구조나 차단 정책이 바뀌면 파싱 로직/헤더를 조정해야 합니다.
"""

import re
import math
import time
import json
import random
import logging
import urllib.parse
from typing import Dict, List, Any, Iterable, Optional, Tuple
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass

from crawling.crawl_lawd_codes_db_utils import search_crawl_lawd_codes
from crawling.apt_mobile_db_utils import apt_save_to_sqlite

# -----------------------------
# 설정값
# -----------------------------
RLET_TP_CDS_DEFAULT = "SG"            # 상가
TRAD_TP_CDS_DEFAULT = "A1:B1:B2"      # 매매/전세/월세
LAT_MARGIN_DEFAULT = 0.118
LON_MARGIN_DEFAULT = 0.111
TIMEOUT = 15
MAX_RETRY = 3
BACKOFF_BASE = 1.4

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_6_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 12; SM-G991N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0",
]

# 간단 랜덤 쿠키 시드 (굳이 로그인 필요 없음)
COOKIE_POOL = [
    {"NNB": "1{}".format(random.randrange(10**10, 10**11-1)), "ASID": "a{}".format(random.randrange(10**8, 10**9-1))},
    {"NNB": "2{}".format(random.randrange(10**10, 10**11-1)), "ASID": "b{}".format(random.randrange(10**8, 10**9-1))},
    {"NNB": "3{}".format(random.randrange(10**10, 10**11-1)), "ASID": "c{}".format(random.randrange(10**8, 10**9-1))},
]

# -----------------------------
# 데이터 모델
# -----------------------------
@dataclass
class FilterInfo:
    lat: float
    lon: float
    z: int
    cortarNo: str
    rletTpCds: str
    tradTpCds: str

@dataclass
class ArticleItem:
    lawdCd: str             # 법정동코드 (예: '4157010300' - 운양동)"
    umdNm: str              # 읍면동명 (예: '운양동')
    article_no: str             # 물건번호 (예: '2553876297')
    article_name: str         # 물건명 (예: '일반상가', '김포한강신도시 아이파크 상가')
    real_estate_type: str     # 부동산 유형 코드 (예: 'APT', 'VL', 'SG', 'SMS')
    real_estate_name: str     # 부동산 유형 명 (예: '아파트', '빌라', '상가', '사무실')
    trade_type: str           # 거래유형 명 (예: 'A1', 'B1', 'B2')
    trade_name: str           # 거래유형 (예: '매매', '전세', '월세')
    price: str                # 가격 (숫자 또는 문자열, ex: '30000' 또는 '3억') - 단위는 만원
    area1: Optional[float]# 계약면적 (평 단위, = spc1_m2 * 0.3025)
    area2: Optional[float]# 전용면적 (평 단위, = spc2_m2 * 0.3025)
    exclusive_area_pyeong: str  # 전용면적 (평 단위, = spc2_m2 * 0.3025)
    building_name: str          # 건물명 (동명:704동)
    direction: str          # 방향 (예: '남향', '북향', '')
    hanPrc: str             # 보증금/한글가격 표시 (예: '3억 2,000', '1,500')
    rentPrc: str            # 월세 가격 (예: '80', '0')
    flrInfo: str            # 층수 정보 (예: '1/6', '3/7')
    cfloor: str             # 현재층 (예: '1', '3')
    tfloor: str             # 총층 (예: '6', '7')
    tagList: str            # 주요 특징 태그 (예: '급매, 주차가능, 역세권')
    company_name: str       # 중개사명 (예: '보고부동산')
    realtor_name: str       # 중개사무소명 (예: '보고부동산공인중개사사무소')
    latitude: str           # 위도 (예: '37.612345')
    longitude: str          # 경도 (예: '126.705678')
    detail_url: str         # 상세페이지 URL (예: 'https://m.land.naver.com/article/info/2553876297')
    feature_desc: str       # 주요특징 (예: '역세권, 주차가능, 대로변')
    keyword: str            # 검색어(지역명 등) (예: '운양동', '김포시 운양동')

# -----------------------------
# 유틸
# -----------------------------
def rand_headers() -> Dict[str, str]:
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
        "Referer": "https://m.land.naver.com/",
    }

def rand_cookies() -> Dict[str, str]:
    return random.choice(COOKIE_POOL).copy()

def sleep_jitter(a=0.8, b=1.8):
    time.sleep(random.uniform(a, b))

def request_with_retry(session: requests.Session, method: str, url: str, **kwargs) -> requests.Response:
    """간단 재시도 + 지연"""
    last_exc = None
    for attempt in range(1, MAX_RETRY + 1):
        try:
            sleep_jitter(0.5, 1.8)
            resp = session.request(method, url, timeout=TIMEOUT, **kwargs)
            # 차단/오류 시 backoff
            if resp.status_code >= 500 or resp.status_code in (403, 429):
                raise requests.HTTPError(f"HTTP {resp.status_code}")
            return resp
        except Exception as e:
            last_exc = e
            backoff = (BACKOFF_BASE ** attempt) + random.uniform(0.0, 0.6)
            time.sleep(backoff)
    assert last_exc is not None
    raise last_exc

def safe_float(s: Any) -> Optional[float]:
    try:
        if s is None: return None
        return float(str(s).replace(",", "").strip())
    except Exception:
        return None

def m2_to_py(m2: Optional[float]) -> Optional[float]:
    if m2 is None: return None
    return round(m2 * 0.3025, 2)

# === 추가/수정: 진단용 로거 ===
import sys
def dprint(*args):
    print("[DEBUG]", *args, file=sys.stderr)

# === 추가: 검색어 정규화(시/구/동이 섞인 경우 동 단위 우선) ===
def normalize_keyword(keyword: str) -> str:
    """
    더 이상 동/읍/면/리로 축약하지 않고, 사용자가 준(또는 DB에서 온)
    전체 지명을 그대로 사용한다.
    """
    return keyword.strip()

# -----------------------------
# (1) 검색 페이지 가져오기
# -----------------------------
def fetch_search_page(session: requests.Session, keyword: str, verify: bool=False) -> str:
    enc = urllib.parse.quote(keyword.strip())
    url = f"https://m.land.naver.com/search/result/{enc}"
    if verify:
        dprint(f"[검색] 키워드='{keyword}', URL={url}")
    resp = request_with_retry(session, "GET", url, headers=rand_headers())
    resp.raise_for_status()
    if verify:
        dprint(f"[검색] status={resp.status_code}, len(html)={len(resp.text)}")
    return resp.text

# -----------------------------
# (2) filter 블록 파싱
# -----------------------------
FILTER_BLOCK_RE = re.compile(
    r"filter:\s*\{(?P<body>.*?)\}", re.DOTALL
)
def parse_filter(html: str, verify: bool=False) -> FilterInfo:
    m = FILTER_BLOCK_RE.search(html)
    if not m:
        # 스크립트 최소화/구조 변화 대비: 텍스트로 한 번 더 탐색
        soup = BeautifulSoup(html, "lxml")
        txt = soup.get_text(" ", strip=False)
        m = FILTER_BLOCK_RE.search(txt)

    if not m:
        raise ValueError("filter 블록을 찾지 못했습니다. (페이지 구조 변경 가능)")

    raw = m.group("body")
    cleaned = raw.replace(" ", "").replace("'", "").replace('"', "")

    def pick(key: str, default: str = "") -> str:
        try:
            return cleaned.split(f"{key}:")[1].split(",")[0]
        except Exception:
            return default

    lat_s = pick("lat"); lon_s = pick("lon"); z_s = pick("z","12")
    cortarNo = pick("cortarNo")
    rletTpCds = pick("rletTpCds","*") or "*"
    tradTpCds = pick("tradTpCds","A1:B1:B2") or "A1:B1:B2"

    # 타입/값 검증
    try:
        lat = float(lat_s); lon = float(lon_s)
    except Exception:
        raise ValueError(f"lat/lon 파싱 실패: lat='{lat_s}', lon='{lon_s}'")

    try:
        z = int(z_s or "12")
    except Exception:
        z = 12

    if not cortarNo or not cortarNo.isdigit():
        raise ValueError(f"cortarNo 이상: '{cortarNo}'")

    if verify:
        dprint(f"[filter] lat={lat}, lon={lon}, z={z}, cortarNo={cortarNo}, rletTpCds='{rletTpCds}', tradTpCds='{tradTpCds}'")

    return FilterInfo(lat=lat, lon=lon, z=z, cortarNo=cortarNo,
                      rletTpCds=rletTpCds, tradTpCds=tradTpCds)

# -----------------------------
# (3) 클러스터(원형 그룹) 리스트 호출
# -----------------------------
def build_bounds(lat: float, lon: float,
                 lat_margin: float = LAT_MARGIN_DEFAULT,
                 lon_margin: float = LON_MARGIN_DEFAULT) -> Tuple[float, float, float, float]:
    btm = lat - lat_margin
    top = lat + lat_margin
    lft = lon - lon_margin
    rgt = lon + lon_margin
    return btm, lft, top, rgt

def build_cluster_list_url(f: FilterInfo,
                           rletTpCds: Optional[str] = None,
                           tradTpCds: Optional[str] = None,
                           lat_margin: float = LAT_MARGIN_DEFAULT,
                           lon_margin: float = LON_MARGIN_DEFAULT) -> str:
    rlet = rletTpCds or RLET_TP_CDS_DEFAULT
    trad = tradTpCds or TRAD_TP_CDS_DEFAULT
    btm, lft, top, rgt = build_bounds(f.lat, f.lon, lat_margin, lon_margin)
    return (
        "https://m.land.naver.com/cluster/clusterList?"
        f"view=atcl&cortarNo={f.cortarNo}&rletTpCd={rlet}&tradTpCd={trad}"
        f"&z={f.z}&lat={f.lat}&lon={f.lon}&btm={btm}&lft={lft}&top={top}&rgt={rgt}"
    )

def fetch_cluster_list(session: requests.Session, url: str, verify: bool=False) -> Dict[str, Any]:
    if verify:
        dprint(f"[clusterList] GET {url}")
    resp = request_with_retry(session, "GET", url, headers=rand_headers(), cookies=rand_cookies())
    resp.raise_for_status()
    data = resp.json()
    if verify:
        sizes = {
            "ARTICLE": len(data.get("data", {}).get("ARTICLE", []) or []),
            "COMPLEX": len(data.get("data", {}).get("COMPLEX", []) or []),
            "REGION":  len(data.get("data", {}).get("REGION", []) or []),
        }
        dprint(f"[clusterList] status={resp.status_code}, sizes={sizes}")
    return data

# -----------------------------
# (4) 그룹(원형)별 매물 리스트 페이지네이션 호출
# -----------------------------
def build_article_list_url(lgeo: str, rletTpCds: str, tradTpCds: str,
                           z: int, lat: float, lon: float, total_cnt: int,
                           cortarNo: str, page: int) -> str:
    return (
        "https://m.land.naver.com/cluster/ajax/articleList?"
        f"itemId={lgeo}&mapKey=&lgeo={lgeo}&showR0=&"
        f"rletTpCd={rletTpCds}&tradTpCd={tradTpCds}&z={z}&lat={lat}&"
        f"lon={lon}&totCnt={total_cnt}&cortarNo={cortarNo}&page={page}"
    )

def iter_group_pages(session: requests.Session, group: Dict[str, Any],
                     rletTpCds: str, tradTpCds: str, cortarNo: str, verify: bool=False) -> Iterable[Dict[str, Any]]:
    lgeo = group.get("lgeo")
    count = int(group.get("count", 0))
    z = int(group.get("z", 12))
    lat = float(group.get("lat", 0))
    lon = float(group.get("lon", 0))
    max_page = math.ceil(count / 20) if count else 0
    if verify:
        dprint(f"[group] lgeo={lgeo}, count={count}, pages={max_page}, z={z}, lat={lat}, lon={lon}")
    for page in range(1, max_page + 1):
        #================================
        # 실제  호출및 데이타 가져오기 (랜덤 지연 + JSON 정규화)
        time.sleep(random.uniform(30, 60))  # 10~20초 랜덤 대기 (차단 회피)
        #
        url = build_article_list_url(lgeo, rletTpCds, tradTpCds, z, lat, lon, count, cortarNo, page)
        if verify:
            dprint(f"[articleList] page={page} → {url}")
        # ================================
        # 실제  호출및 데이타 가져오기
        #resp = request_with_retry(session, "GET", url, headers=rand_headers(), cookies=rand_cookies())
        resp = session.get(url, headers=rand_headers())
        resp.raise_for_status()
        yield resp.json()           # 밖으로 응답반환하면서 내부적으로는 처리함. return은 1번처리로 끝남
        #return [resp.json()]

# -----------------------------
# (5) JSON 파싱 → ArticleItem
# -----------------------------
def parse_articles(session: requests.Session, payload: Dict[str, Any], keyword: str, lawdCd: str) -> List[ArticleItem]:
    #print(f"[parse_articles] payload keys={list(payload.keys()) if isinstance(payload, dict) else type(payload)}")
    """
    /cluster/ajax/articleList 응답에서 매물 정보 추출
    - 대응 형태:
      A) {"body": [ {...}, ... ]}
      B) {"body": {"articleList": [ {...}, ... ]}}
      C) {"list": [ {...}, ... ]}
      D) [ {...}, ... ]  # 루트가 리스트인 경우
    """
    items: List[ArticleItem] = []

    # ---- 후보 리스트(candidates) 안전 추출 ----
    candidates: List[Dict[str, Any]] = []

    if isinstance(payload, dict):
        body = payload.get("body")
        if isinstance(body, list):
            candidates = body
        elif isinstance(body, dict):
            if isinstance(body.get("articleList"), list):
                candidates = body["articleList"]
            elif isinstance(body.get("list"), list):
                candidates = body["list"]
        if not candidates and isinstance(payload.get("list"), list):
            candidates = payload["list"]
    elif isinstance(payload, list):
        candidates = payload

    if not isinstance(candidates, list) or not candidates:
        return items

    # ---- 매물 파싱 ----
    for v in candidates:
        if not isinstance(v, dict):
            continue

        article_no       = str(v.get("atclNo", "") or "")
        article_name     = str(v.get("atclNm", "") or "")       # 일반상가
        real_estate_type = str(v.get("rletTpCd", "") or "")     # 'APT' → "아파트", 'VL' → "빌라", 'SG' → "상가", 'SMS' → "사무실"
        real_estate_name = str(v.get("rletTpNm", "") or "")     # 'APT' → "아파트", 'VL' → "빌라", 'SG' → "상가", 'SMS' → "사무실"
        trade_type   = str(v.get("tradTpCd", "") or "")         # 'A1' → "매매", 'B1' → "전세", 'B2' → "월세"
        trade_name   = str(v.get("tradTpNm", "") or "")         # 'A1' → "매매", 'B1' → "전세", 'B2' → "월세"

        # 숫자/문자 혼재 대비
        # price: str  # 가격 (숫자 또는 문자열, ex: '30000' 또는 '3억') - 단위는 만원
        # hanPrc: str  # 보증금/한글가격 표시 (예: '3억 2,000', '1,500')
        # rentPrc: str  # 월세 가격 (예: '80', '0')
        price   = str(v.get("prc", "") if v.get("prc", "") is not None else "")       # 가격 (만원)
        hanPrc  = str(v.get("hanPrc", "") if v.get("hanPrc", "") is not None else "")   # 한글가격
        rentPrc = str(v.get("rentPrc", "") if v.get("rentPrc", "") is not None else "") # 월세 (만원)

        spc1 = safe_float(v.get("spc1"))    # 계약면적 m2
        spc2 = safe_float(v.get("spc2"))    # 전용면적 m2
        area1 = spc1                        # 계약면적 m2
        area2 = spc2                        # 전용면적 m2
        exclusive_area_pyeong = m2_to_py(area2)     # 전용면적 평
        # 동/방향
        building_name = str(v.get("bildNm", "") or "")      # 건물명(동명:704동)
        direction = str(v.get("direction", "") or "")  # 방향

        # 층수 정보(8/30)
        flrInfo = str(v.get("flrInfo", "") or "")
        cfloor = flrInfo.split("/")[0] if "/" in flrInfo else "" # 현재층
        tfloor = flrInfo.split("/")[1] if "/" in flrInfo else "" # 총층

        # tagList: 리스트/문자 혼재
        tag_raw = v.get("tagList")
        if isinstance(tag_raw, list):
            tag_list = ", ".join([str(t) for t in tag_raw])
        else:
            tag_list = str(tag_raw) if tag_raw is not None else ""
        # 주요특징
        feature_desc = str(v.get("atclFetrDesc", "") or "") # 주요특징
        company_name = str(v.get("cpNm", "") or "")
        realtor_name = str(v.get("rltrNm", "") or "")
        # 위도/경도
        latitude = str(v.get("lat", "") or "")
        longitude = str(v.get("lng", "") or "")

        # 상세 URL
        detail_url = f"https://m.land.naver.com/article/info/{article_no}" if article_no else ""

        # 예: "경기도 김포시 운양동" → "운양동"
        umdNm = keyword.split()[-1]
        items.append(ArticleItem(
            lawdCd=lawdCd[0:5],
            umdNm=umdNm,
            article_no=article_no,
            article_name=article_name,
            real_estate_type=real_estate_type,              # 'APT', 'VL', 'SG', 'SMS'
            real_estate_name=real_estate_name,              # '아파트', '빌라', '상가', '사무실'
            trade_type=trade_type,                          # 'A1', 'B1', 'B2'
            trade_name=trade_name,                          # '매매', '전세', '월세'
            price=price,
            area1=area1,
            area2=area2,
            exclusive_area_pyeong=exclusive_area_pyeong,    # 전용면적 평
            building_name=building_name,
            direction=direction,
            hanPrc=hanPrc,
            rentPrc=rentPrc,
            flrInfo=flrInfo,
            cfloor=cfloor,
            tfloor=tfloor,
            tagList=tag_list,
            company_name=company_name,
            realtor_name=realtor_name,
            latitude=latitude,
            longitude=longitude,
            detail_url=detail_url,
            feature_desc=feature_desc,
            keyword=keyword,
        ))

    # 필요 시 즉시 확인
    print_articles(items)

    # DB 저장 예시 (필요 시)
    savd_db_dict(session, items, page=1, keyword=keyword)

    return items

# -----------------------------
# (6) 화면(터미널) 목록 출력
# -----------------------------
def print_articles(items: List[ArticleItem], limit: Optional[int] = None):
    if not items:
        print("표시할 데이터가 없습니다.")
        return
    print("=" * 120)
    print(f"{'법정코드':<8} {'키워드':<8} {'물건번호':<12} {'유형':<6} {'거래':<4} {'가격':<10} {'보증금':<10} {'월세':<8} {'계약(평)':<10} {'전용(평)':<10} {'층수':<12} {'방향':<12}  {'중개사':<18} {'비고':<18}  {'상세URL'}")
    print("-" * 120)
    count = 0
    for it in items:
        count += 1
        if limit and count > limit: break
        print(
            f"{it.lawdCd:<8} {it.keyword:<8} {it.article_no:<12} {it.real_estate_name:<6} {it.trade_name:<4} {it.price:<10} "
            f"{it.hanPrc:<10} {it.rentPrc:<8} "
            f"{(str(it.area1) if it.area1 is not None else ''):<10} "
            f"{(str(it.area2) if it.area2 is not None else ''):<10} "
            f"{it.flrInfo:<12} {it.direction:<12} {it.realtor_name:<18}  {it.feature_desc:<20} {it.detail_url}"
        )
    print("=" * 120)
    print(f"총 {min(count, len(items))}건 표시 (전체 {len(items)}건)")

# -----------------------------
# DB 저장 예시
def savd_db_dict(session: requests.Session, items: List[ArticleItem], page: int, keyword: str):
    """
    ArticleItem 리스트(items)를 받아 DB 저장용 dict 리스트를 구성 후 apt_save_to_sqlite()로 저장
    """
    if not items:
        print("저장할 데이터가 없습니다.")
        return

    data_entries = []

    for it in items:
        # 안전하게 속성 추출
        lawdCd = getattr(it, "lawdCd", "")
        umdNm = getattr(it, "umdNm", keyword)
        article_no = getattr(it, "article_no", "")
        article_name = getattr(it, "article_name", getattr(it, "rletTpNm", ""))
        real_estate_type = getattr(it, "real_estate_type", getattr(it, "rletTpCd", ""))
        real_estate_name = getattr(it, "real_estate_name", getattr(it, "rletTpNm", ""))
        trade_type = getattr(it, "trade_type", getattr(it, "tradTpCd", ""))
        trade_name = getattr(it, "trade_name", getattr(it, "tradTpNm", ""))
        price = getattr(it, "price", "")
        area1 = getattr(it, "area1", "")
        area2 = getattr(it, "area2", "")
        exclusive_area_pyeong = getattr(it, "exclusive_area_pyeong", "")
        building_name = getattr(it, "building_name", "")
        direction = getattr(it, "direction", "")
        hanPrc = getattr(it, "hanPrc", "")
        rentPrc = getattr(it, "rentPrc", "")
        flrInfo = getattr(it, "flrInfo", "")
        cfloor = flrInfo.split("/")[0] if "/" in flrInfo else flrInfo
        tfloor = flrInfo.split("/")[1] if "/" in flrInfo else ""
        tag_list = getattr(it, "tagList", "")
        company_name = getattr(it, "company_name", "")
        realtor_name = getattr(it, "rltrNm", "")
        latitude = getattr(it, "lat", "")
        longitude = getattr(it, "lon", "")
        detail_url = getattr(it, "detail_url", "")
        feature_desc = getattr(it, "feature_desc", "")

        # 상세페이지에서 보증금/월세 정보 추출 (필요 시)
        sale_deposit_price = hanPrc
        sale_rent_price = rentPrc
        # if trade_type == "매매":
        #     parse_detail_url = "https://fin.land.naver.com/articles/" + article_no
        #     json_data = extract_next_data(session, parse_detail_url)
        #     if json_data:
        #         price_info = extract_price_info_from_dehydrated_state(json_data)
        #         if price_info:
        #             sale_deposit_price, sale_rent_price = print_price_info(price_info)

        # === dict 구조 (요청된 구조와 동일하게) ===
        # 숫자/문자 혼재 대비
        # price: str  # 가격 (숫자 또는 문자열, ex: '30000' 또는 '3억') - 단위는 만원
        # hanPrc: str  # 보증금/한글가격 표시 (예: '3억 2,000', '1,500')
        # rentPrc: str  # 월세 가격 (예: '80', '0')
        data_entry = {
            "page": page,
            "lawdCd": lawdCd,
            "umdNm": umdNm,
            "confirm_date_str": time.strftime("%Y-%m-%d"),
            "article_no": article_no,
            "article_name": article_name,
            "real_estate_type": real_estate_type,            # 'APT', 'VL', 'SG', 'SMS'
            "real_estate_name": real_estate_name,            # '아파트', '빌라', '상가', '사무실'
            "trade_type": trade_type,                        # 'A1', 'B1', 'B2'
            "trade_name": trade_name,                        # '매매', '전세', '월세'
            "price": price,                                  # 가격 (숫자 또는 문자열, ex: '30000' 또는 '3억') - 단위는 만원
            "area1": area1,
            "area2": area2,
            "exclusive_area_pyeong": exclusive_area_pyeong,  # 전용면적 평
            "building_name": building_name,
            "direction": direction,
            "hanPrc": hanPrc,                                # 보증금/한글가격 표시 (예: '3억 2,000', '1,500')
            "rentPrc": rentPrc,                              # 월세 가격 (예: '80', '0')
            "flrInfo": flrInfo,
            "cfloor": cfloor,
            "tfloor": tfloor,
            "tagList": tag_list,
            "company_name": company_name,
            "realtor_name": realtor_name,
            "latitude": latitude,
            "longitude": longitude,
            "detail_url": detail_url,
            "feature_desc": feature_desc,
            "sale_deposit_price": sale_deposit_price,                   # 보증금/한글가격 표시 (예: '3억 2,000', '1,500')
            "sale_rent_price": sale_rent_price,                     # 월세 가격 (예: '80', '0')
        }
        data_entries.append(data_entry)

    # === DB 저장 ===
    try:
        apt_save_to_sqlite(data_entries)
        print(f"DB 저장 완료: {len(data_entries)}건 (page={page}, {keyword})")
    except Exception as e:
        print(f"⚠ DB 저장 실패 ({keyword}): {e}")

# 상세정보에 해당하는 내역을 가져옴.
def extract_next_data(session: requests.Session, url):
    #headers = get_random_headers()
    response = session.get(url, headers=rand_headers())
    if response.status_code != 200:
        print(f"웹페이지를 가져오지 못했습니다: {response.status_code}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    script_tag = soup.find("script", id="__NEXT_DATA__")
    if not script_tag:
        print("JSON 데이터가 포함된 스크립트 태그를 찾을 수 없습니다.")
        return None

    try:
        data = json.loads(script_tag.string)
        return data
    except json.JSONDecodeError as e:
        print("JSON 파싱 중 오류 발생:", e)
        return None

def extract_price_info_from_dehydrated_state(json_data):
    try:
        queries = json_data['props']['pageProps']['dehydratedState']['queries']
    except KeyError as e:
        print("dehydratedState 또는 queries를 찾을 수 없습니다:", e)
        return None

    for query in queries:
        try:
            result = query['state']['data']['result']
            if isinstance(result, dict) and 'priceInfo' in result:
                return result['priceInfo']
        except KeyError:
            continue

    print("priceInfo를 찾을 수 없습니다.")
    return None

def print_price_info(price_info):
    sale_deposit_price = convert_to_korean_amount(price_info.get("previousDeposit") / 10000) or 0
    sale_rent_price = price_info.get("previousMonthlyRent") // 10000 or 0
    return sale_deposit_price, sale_rent_price

def convert_to_korean_amount(amount):
    try:
        amount = int(amount)
    except Exception:
        return ""
    result = ""
    if amount >= 10000:
        eok = amount // 10000
        remainder = amount % 10000
        result = f"{eok}억"
        if remainder >= 1000:
            chun = remainder // 1000
            result += f"{chun}천"
    elif amount >= 1000:
        chun = amount // 1000
        remainder = amount % 1000
        result = f"{chun}천"
        if remainder >= 100:
            baek = remainder // 100
            result += f"{baek}백"
    elif amount >= 100:
        result = f"{amount // 100}백"
    else:
        result = str(amount)
    return result

# -----------------------------
# (전체 파이프라인)
# -----------------------------
def scrape_one_keyword(session: requests.Session,
                       keyword: str,
                       lawdCd: str,
                       rletTpCds: str = RLET_TP_CDS_DEFAULT,
                       tradTpCds: str = TRAD_TP_CDS_DEFAULT,
                       lat_margin: float = LAT_MARGIN_DEFAULT,
                       lon_margin: float = LON_MARGIN_DEFAULT,
                       verify: bool = False) -> List[ArticleItem]:
    html = fetch_search_page(session, keyword, verify=verify)
    try:
        filt = parse_filter(html, verify=verify)
    except Exception as e:
        if verify:
            dprint(f"[검증실패] filter 파싱 오류: {e}")
        raise

    rlet = rletTpCds or filt.rletTpCds or RLET_TP_CDS_DEFAULT
    trad = tradTpCds or filt.tradTpCds or TRAD_TP_CDS_DEFAULT

    # 줌/마진을 달리하며 최대 4회 진단 시도
    z_candidates = [filt.z, max(6, filt.z - 1), filt.z + 1]
    margin_candidates = [(lat_margin, lon_margin), (lat_margin*1.4, lon_margin*1.4)]

    last_cluster = None
    groups = []
    for z_try in z_candidates:
        for (lat_m, lon_m) in margin_candidates:
            # z만 바꿔서 호출
            f_try = FilterInfo(lat=filt.lat, lon=filt.lon, z=z_try,
                               cortarNo=filt.cortarNo, rletTpCds=filt.rletTpCds, tradTpCds=filt.tradTpCds)
            cluster_url = build_cluster_list_url(f_try, rlet, trad, lat_m, lon_m)
            data = fetch_cluster_list(session, cluster_url, verify=verify)
            last_cluster = data
            groups = data.get("data", {}).get("ARTICLE", []) or []
            if groups:
                if verify:
                    dprint(f"[성공] 그룹 발견: z={z_try}, lat_m={lat_m}, lon_m={lon_m}, groups={len(groups)}")
                break
            else:
                if verify:
                    dprint(f"[무매물] ARTICLE=0 (z={z_try}, lat_m={lat_m}, lon_m={lon_m})")
        if groups:
            break

    if not groups:
        if verify:
            dprint(f"[최종진단] 클러스터 그룹이 없습니다. "
                   f"(키워드='{keyword}', rlet='{rlet}', trad='{trad}', "
                   f"z시도={z_candidates}, margin시도={margin_candidates})")
        return []

    all_items: List[ArticleItem] = []
    for g in groups:
        for payload in iter_group_pages(session, g, rlet, trad, filt.cortarNo, verify=verify):
            items = parse_articles(session, payload, normalize_keyword(keyword), lawdCd)
            all_items.extend(items)

    if verify:
        dprint(f"[결과] '{keyword}' 수집 {len(all_items)}건")
    return all_items

def scrape_keywords(keywords: Dict[str, str],
                    rletTpCds: str = RLET_TP_CDS_DEFAULT,
                    tradTpCds: str = TRAD_TP_CDS_DEFAULT,
                    lat_margin: float = LAT_MARGIN_DEFAULT,
                    lon_margin: float = LON_MARGIN_DEFAULT,
                    verify: bool = False) -> List[ArticleItem]:
    session = requests.Session()
    session.headers.update(rand_headers())
    session.cookies.update(rand_cookies())

    all_results: List[ArticleItem] = []
    for kw, lawdCd in keywords.items():
        print(f"\n▶ 키워드 처리 시작: {kw}")
        try:
            items = scrape_one_keyword(session, kw, lawdCd, rletTpCds, tradTpCds, lat_margin, lon_margin, verify=verify)
            print(f"▶ 키워드 처리 완료: {kw} (수집 {len(items)}건)")
            if not items and verify:
                print(f"[{kw}] 검증 결과: ARTICLE 없음 → 동 단위 검색어/줌/마진 조정 후에도 매물 미발견.")
            all_results.extend(items)
        except Exception as e:
            print(f"⚠ 키워드 처리 실패: {kw} -> {e}")
        sleep_jitter(1.2, 2.5)
    return all_results


# 테이블에서 검색어로 법정동 코드 조회후 keywords 딕셔너리 생성
def make_keywords_from_search(name_like: str = "", trade_type: str="APT") -> Dict[str, str]:
    """
    search_lawd_codes() 결과를 읽어 keywords 딕셔너리를 생성한다.
    예:
        {"운양동": "4157010300", "장기동": "4157010400"}
    """
    # 1️⃣ search_crawl_lawd_codes()로 DB조회
    rows = search_crawl_lawd_codes(lawd_name=name_like, trade_type=trade_type)

    if not rows:
        print("⚠️ 검색 결과가 없습니다.")
        return {}

    # 2️⃣ 결과를 {동이름: 코드} 형태로 변환
    keywords = {}
    for row in rows:
        full_name = row["lawd_name"].strip()
        # 예: "경기도 김포시 운양동" → "운양동"
        short_name = full_name.split()[-1]
        keywords[full_name] = row["lawd_cd"]

    # 3️⃣ 보기 좋게 출력
    print("\n[생성된 keywords]")
    for k, v in keywords.items():
        print(f'"{k}": "{v}",')

    return keywords

# -----------------------------
# 실행 예시
# -----------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    # (예) 여러 지역을 한 번에 처리 (원하시는 만큼 추가)
    # keywords = {
    #     "운양동": "4157010300",
    # }
    # (예) "운양동"이 포함된 데이터만 가져와 keywords 생성
    keywords = make_keywords_from_search(name_like="", trade_type="APT")

    # 상가(SG:APT), 매매/전세/월세(A1:B1:B2) 고정. 필요 시 인자 바꿔 호출.
    results = scrape_keywords(
        keywords,
        rletTpCds="APT",
        tradTpCds="A1:B1:B2",
        lat_margin=0.118,
        lon_margin=0.111,
        verify=True
    )

    # (6) 화면 출력
    # print_articles(results, limit=None)