# -*- coding: utf-8 -*-
import requests
import xmltodict
import datetime
import json
from collections import OrderedDict

from common.vworld_utils import VWorldGeocoding
from pubdata.public_land_lawd_code_db_utils import get_lawd_by_code
from pubdata.public_land_apt_db_utils import init_apt_db, read_apt_db, insert_apt_items
from pubdata.public_land_sanga_db_utils import init_sanga_db, insert_sanga_items, read_sanga_db
from pubdata.public_land_villa_db_utils import init_villa_db, read_villa_db, insert_villa_items
from config import MAP_API_KEY, VWORLD_URL

# ======================================
# 아파트/빌라/상가/비주거 월검색 API => json방식
#========================================
def fetch_land_month(url: str, params: dict, lawd_cd: str, lawd_nm: str, umd_nm: str, year: int, month: int, verify: bool = False):
    """상가/비주거 월별 조회 (JSON -> dict)"""
    month_str = f"{month:02d}"
    params["DEAL_YMD"] = f"{year}{month_str}"
    params["_type"] = "json"
    print(f"fetch_land_month 조회: {lawd_cd}, {lawd_nm}, {umd_nm}, {year}, {month}, {month_str}")

    response = requests.get(url, params=params, verify=verify)
    if response.status_code != 200:
        print(f"{year}년 {month_str}월: API 요청 실패: {response.status_code}, 응답 내용: {response.text}")
        return []

    try:
        response_data = response.json().get("response", {})
        body = response_data.get("body", {})
        items = body.get("items", {})

        if not items or not isinstance(items, dict) or "item" not in items:
            print(f"{year}년 {month_str}월: 검색된 데이터가 없습니다.")
            return []

        items = items["item"]
        if isinstance(items, dict):
            items = [items]

        items_sorted = sorted(
            items,
            key=lambda x: (x.get("dealYear", ""), x.get("dealMonth", ""), x.get("dealDay", ""))
        )

        # 👉 특정 시군구명(sgg_nm)만 필터링
        # 읍면동 공백 대비(트림) like개념 적용
        # ex)파주읍 이면 파주읍 봉암리, 파주리, 백석리등
        umd_nm = (umd_nm or "").strip()
        filtered_items = [
            it for it in items_sorted
            if (it.get("umdNm") or "").startswith(umd_nm)
        ]

        # 각 item에 위도/경도 추가
        for it in filtered_items:
            it["sggNm"] = lawd_nm   # 시군구명(서울시 종로구)
            umdNm = it.get("umdNm", "")
            jibun = it.get("jibun", "")
            # 전체 주소 조합및 geocoding
            address = f"{lawd_nm} {umdNm} {jibun}"
            print(f"Geocoding address: {address}")
            geo = geocode_vworld(address)
            it["lat"] = str(geo["lat"])
            it["lon"] = str(geo["lng"])

        return filtered_items

    except Exception as e:
        print(f"{year}년 {month_str}월: JSON 파싱 오류: {e}")
        print(f"응답 원본: {response.text[:1000]}")
        return []

# // vWorld 지오코딩 래퍼-api호출은 tash서버에서 처리함
def geocode_vworld(address: str, address_type: str = "parcel") -> dict[str, float]:
    """
    vWorldGeocoding 클래스를 사용한 좌표 변환
    :param address: 주소 문자열
    :param address_type: "parcel"(지번) | "road"(도로명)
    :return: {"lat": float, "lng": float}
    """

    try:
        if not address or "*" in address:
            return {"lat": 0.0, "lng": 0.0}

        geo_service = VWorldGeocoding(MAP_API_KEY)

        # =========================
        # 🔥 입력받은 타입 사용
        # =========================
        lat, lng = geo_service.get_lat_lng(address, address_type=address_type)

        if lat is None or lng is None:
            print("Geocode failed:", address)
            return {"lat": 0.0, "lng": 0.0}

        return {
            "lat": float(lat),
            "lng": float(lng)
        }

    except Exception as e:
        print("geocode_vworld error:", e)
        return {"lat": 0.0, "lng": 0.0}


# ==============================
# 국토부실거래 상가 (SANGA) 전체 실행
# ==============================
def run_sanga(lawd_cd: str, lawd_nm:str, umd_nm: str,  years_count: int = 2, verify: bool = False):
    # 1) DB 초기화(테이블 생성)
    init_sanga_db()

    # ✅ 선택한 년수(1/2/3)에 맞춰 대상 연도 리스트 생성
    #    예) years_count=1 -> [2026]
    #        years_count=2 -> [2026, 2025]
    #        years_count=3 -> [2026, 2025, 2024]
    current_year = datetime.datetime.now().year
    years_count = max(1, min(3, int(years_count)))  # 1~3만 허용
    years = [current_year - i for i in range(years_count)]
    #
    current_month_now = datetime.datetime.now().month # 현재 월
    #
    all_items = []
    for year in years:
        """상가/비주거 1개년 전체 조회"""
        url = "http://apis.data.go.kr/1613000/RTMSDataSvcNrgTrade/getRTMSDataSvcNrgTrade"
        #url = "https://apis.data.go.kr/1613000/RTMSDataSvcNrgTrade/getRTMSDataSvcNrgTrade"
        service_key = "B2BtWbuZVFz/EJoLsrDa6corOwSR4SsGwjBKzK2WJQ3JVwRMIUoXOGY3BHXrxZq78nP+ECsW5wB4TEwbgxS2PA=="
        params = {
            "serviceKey": service_key,
            "LAWD_CD": lawd_cd,
            "DEAL_YMD": f"{year}01",
            "pageNo": 1,
            "numOfRows": 1000
        }
        year_items = []

        # ✅ 과거 연도면 12월, 현재 연도면 현재 월
        current_month = 11 if year < current_year else current_month_now
        # 년도별 월별조회
        for month in range(1, current_month + 1):
            # 매 반복마다 params 복사본 생성(사이드이펙트 방지)
            params_month = dict(params)
            # 1) DB 먼저 조회-(읍면동, 년도비교로 존재여부 체크)
            month_items = read_sanga_db(lawd_cd, umd_nm, year, month)
            if month_items:
                print(f"{year}년 : DB에서 {month}월 {len(month_items)}건 조회됨")
                #
                year_items.extend(month_items)
                all_items.extend(month_items)
            else:
                print(f"{year}년 {month:02d}월: DB 데이터 없음 → API 요청")
                month_items = fetch_land_month(url, params_month,lawd_cd, lawd_nm, umd_nm, year, month, verify=verify)
                # DB저장
                if month_items:
                    insert_sanga_items(month_items, lawd_cd)  # DB 저장

                #================================
                # 년도및 전체누적
                year_items.extend(month_items)
                all_items.extend(month_items)

        # 2) 년별 결과 출력
        print_sanga_table(year_items, lawd_cd, year, "00")
        print(f"\n[{year}] 총 누적 건수: {len(year_items)}\n")

    return all_items


def print_sanga_table(items: list, lawd_cd: str, year: int, month_str: str) -> None:
    """SANGA 월별 결과를 표 형태로 출력"""
    # 헤더
    print(f"\n=== {year}년 {month_str}월 거래 내역 ===")
    print(
        f"{'순번':<8}{'주소(법정코드)':<14}{'거래년도(dealYear)':<10}{'거래월(dealMonth)':<10}{'거래일(dealDay)':<10}"
        f"{'건축년도(buildYear)':<14}{'건물면적(buildingAr)':<14}{'건물종류(buildingType)':<14}{'건물용도(buildingUse)':<22}"
        f"{'매수구분(buyerGbn)':<14}{'거래금액(dealAmount)':<14}{'부동산업소명(estateAgentSggNm)':<22}"
        f"{'지번(jibun)':<14}{'토지이용(landUse)':<14}{'대지면적(plottageAr)':<14}{'시군구코드(sggCd)':<14}"
        f"{'시군구명(sggNm)':<14}{'읍면동명(umdNm)':<14}"
        f"{'lat':<12}{'lon':<12}"
    )
    print("=" * 200)

    # 행
    for index, item in enumerate(items, 1):
        print(
            f"{str(index):<8}"
            f"{lawd_cd:<14}"
            f"{str(item.get('dealYear', '') or ''):<10}"
            f"{str(item.get('dealMonth', '') or ''):<10}"
            f"{str(item.get('dealDay', '') or ''):<10}"
            f"{str(item.get('buildYear', '') or ''):<14}"
            f"{str(item.get('buildingAr', '') or ''):<14}"
            f"{str(item.get('floor', '') or ''):<14}"
            f"{str(item.get('buildingType', '') or ''):<14}"
            f"{str(item.get('buildingUse', '') or ''):<22}"
            f"{str(item.get('buyerGbn', '') or ''):<14}"
            f"{str(item.get('dealAmount', '') or ''):<14}"
            f"{str(item.get('estateAgentSggNm', '') or ''):<22}"
            f"{str(item.get('jibun', '') or ''):<14}"
            f"{str(item.get('landUse', '') or ''):<14}"
            f"{str(item.get('plottageAr', '') or ''):<14}"
            f"{str(item.get('sggCd', '') or ''):<14}"
            f"{str(item.get('sggNm', '') or ''):<14}"
            f"{str(item.get('umdNm', '') or ''):<14}"
            f"{str(item.get('lat', '') or ''):<12}"
            f"{str(item.get('lon', '') or ''):<12}"
        )


def sanga_items_to_json(items: list, lawd_cd: str) -> list:
    """run_sanga() 결과에서 필요한 필드만 추려 JSON 레코드 리스트로 변환"""
    def s(v):
        # None / 'null' / 공백 등은 빈 문자열로 통일
        if v is None:
            return ""
        v = str(v).strip()
        return "" if v.lower() == "null" else v

    json_records = []
    for item in items:
        rec = OrderedDict([
            ("lawd_cd",              s(lawd_cd)),
            ("dealYear",             s(item.get("dealYear", ""))),
            ("dealMonth",            s(item.get("dealMonth", ""))),
            ("dealDay",              s(item.get("dealDay", ""))),
            ("buildYear",            s(item.get("buildYear", ""))),
            ("buildingAr",           s(item.get("buildingAr", ""))),
            ("floor",                s(item.get("floor", ""))),
            ("buildingType",         s(item.get("buildingType", ""))),
            ("buildingUse",          s(item.get("buildingUse", ""))),
            ("buyerGbn",             s(item.get("buyerGbn", ""))),
            ("dealAmount",           s(item.get("dealAmount", ""))),
            ("estateAgentSggNm",     s(item.get("estateAgentSggNm", ""))),
            ("jibun",                s(item.get("jibun", ""))),
            ("landUse",              s(item.get("landUse", ""))),
            ("plottageAr",           s(item.get("plottageAr", ""))),
            ("sggCd",                s(item.get("sggCd", ""))),
            ("sggNm",                s(item.get("sggNm", ""))),
            ("umdNm",                s(item.get("umdNm", ""))),
            ("lat",                  s(item.get("lat", ""))),
            ("lon",                  s(item.get("lon", ""))),
        ])
        json_records.append(rec)

    return json_records


# ==============================
# 국토부실거래 빌라 (Villa) 전체 실행
# ==============================
def run_villa(lawd_cd: str, lawd_nm:str, umd_nm: str, years_count: int = 2,  verify: bool = False):
    # 1) DB 초기화(테이블 생성)
    init_villa_db()

    # ✅ 선택한 년수(1/2/3)에 맞춰 대상 연도 리스트 생성
    #    예) years_count=1 -> [2026]
    #        years_count=2 -> [2026, 2025]
    #        years_count=3 -> [2026, 2025, 2024]
    current_year = datetime.datetime.now().year
    years_count = max(1, min(3, int(years_count)))  # 1~3만 허용
    years = [current_year - i for i in range(years_count)]
    #
    current_month_now = datetime.datetime.now().month # 현재 월
    #
    all_items = []
    for year in years:
        # """상가/비주거 1개년 전체 조회"""
        url = "http://apis.data.go.kr/1613000/RTMSDataSvcNrgTrade/getRTMSDataSvcNrgTrade"
        #"""빌라 1개년 전체 조회"""
        # url = "https://apis.data.go.kr/1613000/RTMSDataSvcRHTrade/getRTMSDataSvcRHTrade"
        service_key = "B2BtWbuZVFz/EJoLsrDa6corOwSR4SsGwjBKzK2WJQ3JVwRMIUoXOGY3BHXrxZq78nP+ECsW5wB4TEwbgxS2PA=="
        params = {
            "serviceKey": service_key,
            "LAWD_CD": lawd_cd,
            "DEAL_YMD": f"{year}01",
            "pageNo": 1,
            "numOfRows": 1000
        }
        year_items = []
        # ✅ 과거 연도면 12월, 현재 연도면 현재 월
        current_month = 12 if year < current_year else current_month_now
        # 년도별 월별조회
        for month in range(1, current_month + 1):
            # 매 반복마다 params 복사본 생성(사이드이펙트 방지)
            params_month = dict(params)
            # 1) DB 먼저 조회-(읍면동, 년도,월비교로 존재여부 체크)
            month_items = read_villa_db(lawd_cd, umd_nm, year, month)
            if month_items:
                print(f"{year}년 : DB에서 {month}월 {len(month_items)}건 조회됨")
                #
                year_items.extend(month_items)
                all_items.extend(month_items)
            else:
                print(f"{year}년 {month:02d}월: DB 데이터 없음 → API 요청")
                month_items = fetch_land_month(url, params_month, lawd_cd, lawd_nm, umd_nm, year, month, verify=verify)
                # DB저장
                if month_items:
                    insert_villa_items(month_items, lawd_cd)  # DB 저장

                #================================
                # 년도및 전체누적
                year_items.extend(month_items)
                all_items.extend(month_items)

        # 2) 년별 결과 출력
        print_villa_table(year_items, lawd_cd, year, "00")
        print(f"\n[{year}] 총 누적 건수: {len(year_items)}\n")

    return all_items


def print_villa_table(items: list, lawd_cd: str, year: int, month_str: str) -> None:
    """SANGA 월별 결과를 표 형태로 출력"""
    # 헤더
    print(f"\n=== {year}년 {month_str}월 거래 내역 ===")
    print(
        f"{'순번':<8}{'주소(법정코드)':<14}{'거래년도(dealYear)':<10}{'거래월(dealMonth)':<10}{'거래일(dealDay)':<10}"
        f"{'건축년도(buildYear)':<14}{'건물면적(excluUseAr)':<14}{'건물종류(buildingType)':<14}{'건물용도(buildingUse)':<22}"
        f"{'매도구분(slerGbn)':<14}{'매수구분(buyerGbn)':<14}{'거래금액(dealAmount)':<14}{'부동산업소명(estateAgentSggNm)':<22}"
        f"{'지번(jibun)':<14}{'토지이용(landUse)':<14}{'대지면적(plottageAr)':<14}{'시군구코드(sggCd)':<14}"
        f"{'시군구명(sggNm)':<14}{'읍면동명(umdNm)':<14}{'mhouseNm':<20}{'houseType':<12} "
        f"{'lat':<12}{'lon':<12}"
    )
    print("=" * 200)

    # 행
    for index, item in enumerate(items, 1):
        print(
            f"{str(index):<8}"
            f"{lawd_cd:<14}"
            f"{str(item.get('dealYear', '') or ''):<10}"
            f"{str(item.get('dealMonth', '') or ''):<10}"
            f"{str(item.get('dealDay', '') or ''):<10}"
            f"{str(item.get('buildYear', '') or ''):<14}"
            f"{str(item.get('excluUseAr', '') or ''):<14}"
            f"{str(item.get('floor', '') or ''):<14}"
            f"{str(item.get('buildingType', '') or ''):<14}"
            f"{str(item.get('buildingUse', '') or ''):<22}"
            f"{str(item.get('slerGbn', '') or ''):<14}"
            f"{str(item.get('buyerGbn', '') or ''):<14}"
            f"{str(item.get('dealAmount', '') or ''):<14}"
            f"{str(item.get('estateAgentSggNm', '') or ''):<22}"
            f"{str(item.get('jibun', '') or ''):<14}"
            f"{str(item.get('landUse', '') or ''):<14}"
            f"{str(item.get('plottageAr', '') or ''):<14}"
            f"{str(item.get('sggCd', '') or ''):<14}"
            f"{str(item.get('sggNm', '') or ''):<14}"
            f"{str(item.get('umdNm', '') or ''):<14}"
            f"{str(item.get('mhouseNm', '') or ''):<20}"
            f"{str(item.get('houseType', '') or ''):<12}"
            f"{str(item.get('lat', '') or ''):<12}"
            f"{str(item.get('lon', '') or ''):<12}"
        )


def villa_items_to_json(items: list, lawd_cd: str) -> list:
    """run_sanga() 결과에서 필요한 필드만 추려 JSON 레코드 리스트로 변환"""
    def s(v):
        # None / 'null' / 공백 등은 빈 문자열로 통일
        if v is None:
            return ""
        v = str(v).strip()
        return "" if v.lower() == "null" else v

    json_records = []
    for item in items:
        rec = OrderedDict([
            ("lawd_cd",              s(lawd_cd)),
            ("dealYear",             s(item.get("dealYear", ""))),
            ("dealMonth",            s(item.get("dealMonth", ""))),
            ("dealDay",              s(item.get("dealDay", ""))),
            ("buildYear",            s(item.get("buildYear", ""))),
            ("excluUseAr",           s(item.get("excluUseAr", ""))),
            ("landAr",               s(item.get("landAr", ""))),
            ("floor",                s(item.get("floor", ""))),
            ("buildingType",         s(item.get("buildingType", ""))),
            ("buildingUse",          s(item.get("buildingUse", ""))),
            ("slerGbn",               s(item.get("slerGbn", ""))),
            ("buyerGbn",             s(item.get("buyerGbn", ""))),
            ("dealAmount",           s(item.get("dealAmount", ""))),
            ("estateAgentSggNm",     s(item.get("estateAgentSggNm", ""))),
            ("jibun",                s(item.get("jibun", ""))),
            ("landUse",              s(item.get("landUse", ""))),
            ("plottageAr",           s(item.get("plottageAr", ""))),
            ("sggCd",                s(item.get("sggCd", ""))),
            ("sggNm",                s(item.get("sggNm", ""))),
            ("umdNm",                s(item.get("umdNm", ""))),
            ("mhouseNm",             s(item.get("mhouseNm", ""))),
            ("houseType",            s(item.get("houseType", ""))),
            ("lat",                  s(item.get("lat", ""))),
            ("lon",                  s(item.get("lon", ""))),
        ])
        json_records.append(rec)

    return json_records

# ==============================
# 국토부실거래 아파트 (Apt) 전체 실행
# ==============================
def run_apt(lawd_cd: str, lawd_nm:str, umd_nm: str, apt_nm:str, years_count: int = 2, verify: bool = False):
    # 1) DB 초기화(테이블 생성)
    init_apt_db()

    # ✅ 선택한 년수(1/2/3)에 맞춰 대상 연도 리스트 생성
    #    예) years_count=1 -> [2026]
    #        years_count=2 -> [2026, 2025]
    #        years_count=3 -> [2026, 2025, 2024]
    current_year = datetime.datetime.now().year
    years_count = max(1, min(3, int(years_count)))  # 1~3만 허용
    years = [current_year - i for i in range(years_count)]
    #
    current_month_now = datetime.datetime.now().month # 현재 월
    #
    all_items = []
    for year in years:
        # """아파트 1개년 전체 조회"""
        # url = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade"
        url = "http://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade"
        service_key = "B2BtWbuZVFz/EJoLsrDa6corOwSR4SsGwjBKzK2WJQ3JVwRMIUoXOGY3BHXrxZq78nP+ECsW5wB4TEwbgxS2PA=="
        params = {
            "serviceKey": service_key,
            "LAWD_CD": lawd_cd,
            "DEAL_YMD": f"{year}01",
            "pageNo": 1,
            "numOfRows": 1000
        }
        year_items = []
        # ✅ 과거 연도면 12월, 현재 연도면 현재 월
        current_month = 12 if year < current_year else current_month_now
        # 년도별 월별조회
        for month in range(1, current_month + 1):
            # 매 반복마다 params 복사본 생성(사이드이펙트 방지)
            params_month = dict(params)
            # 1) DB 먼저 조회-(읍면동, 년도,월비교로 존재여부 체크)
            month_items = read_apt_db(lawd_cd, umd_nm, apt_nm, dealYear=year, dealMonth=month)
            if month_items:
                print(f"{year}년 : DB에서 {month}월 {len(month_items)}건 조회됨")
                #
                year_items.extend(month_items)
                all_items.extend(month_items)
            else:
                print(f"{year}년 {month:02d}월: DB 데이터 없음 → API 요청")
                month_items = fetch_land_month(url, params_month, lawd_cd, lawd_nm, umd_nm, year, month, verify=verify)
                # DB저장
                if month_items:
                    insert_apt_items(month_items, lawd_cd)  # DB 저장

                #================================
                # 년도및 전체누적
                year_items.extend(month_items)
                all_items.extend(month_items)

        # 2) 년별 결과 출력
        print_apt_table(year_items, lawd_cd, year, "전체")
        print(f"\n[{year}] 총 누적 건수: {len(year_items)}\n")

    return all_items


def print_apt_table(items: list, lawd_cd: str, year: int, month_str: str) -> None:
    """SANGA 월별 결과를 표 형태로 출력"""
    # 헤더
    print(f"\n=== {year}년 {month_str}월 거래 내역 ===")
    print(
        f"{'순번':<8}{'주소(법정코드)':<14}{'거래년도(dealYear)':<10}{'거래월(dealMonth)':<10}{'거래일(dealDay)':<10}"
        f"{'건축년도(buildYear)':<14}{'건물면적(excluUseAr)':<14}{'층(floor)':<22}"
        f"{'매도구분(slerGbn)':<14}{'매수구분(buyerGbn)':<14}{'거래금액(dealAmount)':<14}{'부동산업소명(estateAgentSggNm)':<22}"
        f"{'시군구코드(sggCd)':<14}{'시군구명(sggNm)':<14}{'읍면동명(umdNm)':<14}{'aptNm':<20}{'지번(jibun)':<14}{'aptDong':<12} "
        f"{'lat':<12}{'lon':<12}"
    )
    print("=" * 200)

    # 행
    for index, item in enumerate(items, 1):
        print(
            f"{str(index):<8}"
            f"{lawd_cd:<14}"
            f"{str(item.get('dealYear', '') or ''):<10}"
            f"{str(item.get('dealMonth', '') or ''):<10}"
            f"{str(item.get('dealDay', '') or ''):<10}"
            f"{str(item.get('buildYear', '') or ''):<14}"
            f"{str(item.get('excluUseAr', '') or ''):<14}"
            f"{str(item.get('floor', '') or ''):<14}"
            f"{str(item.get('slerGbn', '') or ''):<14}"
            f"{str(item.get('buyerGbn', '') or ''):<14}"
            f"{str(item.get('dealAmount', '') or ''):<14}"
            f"{str(item.get('estateAgentSggNm', '') or ''):<22}"
            f"{str(item.get('sggCd', '') or ''):<14}"
            f"{str(item.get('sggNm', '') or ''):<14}"
            f"{str(item.get('umdNm', '') or ''):<14}"
            f"{str(item.get('aptNm', '') or ''):<20}"
            f"{str(item.get('jibun', '') or ''):<14}"
            f"{str(item.get('aptDong', '') or ''):<12}"
            f"{str(item.get('lat', '') or ''):<12}"
            f"{str(item.get('lon', '') or ''):<12}"
        )

def apt_items_to_json(items: list, lawd_cd: str) -> list:
    """run_sanga() 결과에서 필요한 필드만 추려 JSON 레코드 리스트로 변환"""
    def s(v):
        # None / 'null' / 공백 등은 빈 문자열로 통일
        if v is None:
            return ""
        v = str(v).strip()
        return "" if v.lower() == "null" else v

    json_records = []
    for item in items:
        rec = OrderedDict([
            ("lawd_cd",              s(lawd_cd)),
            ("dealYear",             s(item.get("dealYear", ""))),
            ("dealMonth",            s(item.get("dealMonth", ""))),
            ("dealDay",              s(item.get("dealDay", ""))),
            ("buildYear",            s(item.get("buildYear", ""))),
            ("excluUseAr",           s(item.get("excluUseAr", ""))),
            ("landAr",               s(item.get("landAr", ""))),
            ("floor",                s(item.get("floor", ""))),
            ("slerGbn",              s(item.get("slerGbn", ""))),
            ("buyerGbn",             s(item.get("buyerGbn", ""))),
            ("dealAmount",           s(item.get("dealAmount", ""))),
            ("estateAgentSggNm",     s(item.get("estateAgentSggNm", ""))),
            ("dealingGbn",           s(item.get("dealingGbn", ""))),
            ("rgstDate",             s(item.get("rgstDate", ""))),
            ("sggCd",                s(item.get("sggCd", ""))),
            ("sggNm",                s(item.get("sggNm", ""))),
            ("umdNm",                s(item.get("umdNm", ""))),
            ("aptNm",                s(item.get("aptNm", ""))),
            ("jibun",                s(item.get("jibun", ""))),
            ("aptDong",              s(item.get("aptDong", ""))),
            ("lat",                  s(item.get("lat", ""))),
            ("lon",                  s(item.get("lon", ""))),
        ])
        json_records.append(rec)

    return json_records



# ==============================
# main — 테스트 실행
# ==============================
if __name__ == "__main__":

    #const lawdCd = selectedLawdCd.slice(0, 5);
    #const umdNm = selectedUmdNm;

    lawd_cd = "41480"  # 11110: 서울시 종로구 창신동, 41570-00000: 경기도 김포시 운양동, 4148025326:경기도 파주시 파주읍 파주리
    # 3) 코드로 단건 조회
    res = get_lawd_by_code(lawd_cd + "00000")  # 법정동명(서울특별시 종로구)
    print("[READ]", res)
    lawd_nm = res["lawd_name"]  # 서울특별시 종로구
    # 읍,면,동 개념으로 파주읍 파주리 경우는 목록은 파주읍 파주리, 붕원리등 나오나 파주읍만 드간다(네이버 부동산 검색기준임).
    umd_nm = "파주읍"  # 읍면동(창신동,숭인동, 종로1가, 운양동, 파주읍 등)

    print(f"[main start.] lawd_cd : {lawd_cd} lawd_nm : {lawd_nm} umd_nm : {umd_nm}")

    #=== 상가 테스트 ===
    # 1) DB 초기화(테이블 생성)
   #init_sanga_db()

    years_count = 3  # 최근 2개년

    # print("\n########## SANGA (비주거) ##########")
    # all_items = run_sanga(lawd_cd, lawd_nm, umd_nm, years_count, verify=False)
    # #
    # # (1) all_items를 JSON 타입(리스트[딕셔너리])으로 변환하여
    # json_records = sanga_items_to_json(all_items, lawd_cd)
    # print(json.dumps(json_records, ensure_ascii=False, indent=2))
    # #
    # print(f"\n[상가 총 누적 건수: {len(all_items)}\n")

    #=== 빌라(연릭) 테스트 ===
    # 1) DB 초기화(테이블 생성)
    #init_villa_db()
    #
    # print("\n########## VILLA(빌라/연립등) ##########")
    # all_items = run_villa(lawd_cd, lawd_nm, umd_nm, years_count, verify=False)
    # #
    # # (1) all_items를 JSON 타입(리스트[딕셔너리])으로 변환하여
    # json_records = villa_items_to_json(all_items, lawd_cd)
    # #print(json.dumps(json_records, ensure_ascii=False, indent=2))
    # #
    # print(f"\n[빌라 총 누적 건수: {len(all_items)}\n")

    #=== 아파트 테스트 ===
    # 1) DB 초기화(테이블 생성)
    #init_apt_db()

    print("\n########## APT(아파트) ##########")
    all_items = run_apt(lawd_cd, lawd_nm, umd_nm, "", years_count, verify=False)
    #
    # (1) all_items를 JSON 타입(리스트[딕셔너리])으로 변환하여
    json_records = apt_items_to_json(all_items, lawd_cd)
    #print(json.dumps(json_records, ensure_ascii=False, indent=2))

    print(f"\n[아파트 총 누적 건수: {len(all_items)}\n")