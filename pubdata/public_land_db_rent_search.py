# -*- coding: utf-8 -*-
import requests
import xmltodict
import datetime
import json
from collections import OrderedDict

from common.vworld_utils import VWorldGeocoding
from config import MAP_API_KEY, VWORLD_URL
from pubdata.public_land_apt_rent_db_utils import init_rent_db, read_rent_db, insert_rent_items
from pubdata.public_land_lawd_code_db_utils import get_lawd_by_code


# ==============================
# 국토부 아파트 전월세 API 월검색
# ==============================
def fetch_apt_rent_month(
    url: str,
    params: dict,
    lawd_cd: str,
    lawd_nm: str,
    umd_nm: str,
    apt_nm: str,
    year: int,
    month: int,
    verify: bool = False
):
    """
    아파트 전월세 월별 조회
    API: RTMSDataSvcAptRent
    """
    month_str = f"{month:02d}"
    params["DEAL_YMD"] = f"{year}{month_str}"
    params["_type"] = "json"

    print(f"fetch_apt_rent_month 조회: {lawd_cd}, {lawd_nm}, {umd_nm}, {apt_nm}, {year}, {month_str}")

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/plain, */*"
    }

    response = requests.get(url, headers=headers, params=params, verify=verify)

    print("[APT RENT API URL]", response.url)
    print("[APT RENT STATUS]", response.status_code)
    print("[APT RENT TEXT]", response.text[:500])

    if response.status_code != 200:
        print(f"{year}년 {month_str}월: APT RENT API 요청 실패: {response.status_code}")
        print(f"응답 내용: {response.text[:1000]}")
        return []

    try:
        response_data = response.json().get("response", {})
        body = response_data.get("body", {})
        items = body.get("items", {})

        if not items or not isinstance(items, dict) or "item" not in items:
            print(f"{year}년 {month_str}월: 아파트 전월세 데이터 없음")
            return []

        items = items["item"]

        if isinstance(items, dict):
            items = [items]

        items_sorted = sorted(
            items,
            key=lambda x: (
                str(x.get("dealYear", "") or ""),
                str(x.get("dealMonth", "") or ""),
                str(x.get("dealDay", "") or "")
            )
        )

        umd_nm = (umd_nm or "").strip()
        apt_nm = (apt_nm or "").strip()

        filtered_items = []

        for it in items_sorted:
            item_umd = str(it.get("umdNm", "") or "").strip()
            item_apt = str(it.get("aptNm", "") or "").strip()

            # 읍면동 필터
            if umd_nm and not item_umd.startswith(umd_nm):
                continue

            # 아파트명 필터
            if apt_nm and item_apt != apt_nm:
                continue

            # 시군구명 추가
            it["sggNm"] = lawd_nm

            # 주소 조합
            jibun = str(it.get("jibun", "") or "").strip()
            roadnm = str(it.get("roadnm", "") or "").strip()

            # 도로명이 있으면 도로명 주소 우선, 없으면 지번 주소
            if roadnm:
                address = f"{lawd_nm} {item_umd} {roadnm}"
                address_type = "road"
            else:
                address = f"{lawd_nm} {item_umd} {jibun}"
                address_type = "parcel"

            print(f"[APT RENT] Geocoding address: {address}")

            geo = geocode_vworld(address, address_type=address_type)

            it["lat"] = str(geo["lat"])
            it["lon"] = str(geo["lng"])

            filtered_items.append(it)

        return filtered_items

    except Exception as e:
        print(f"{year}년 {month_str}월: APT RENT JSON 파싱 오류: {e}")
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
# 국토부 아파트 전월세 전체 실행
# ==============================
def run_apt_rent(
    lawd_cd: str,
    lawd_nm: str,
    umd_nm: str,
    apt_nm: str,
    years_count: int = 2,
    verify: bool = False
):
    """
    아파트 전월세 전체 실행 함수.
    DB 먼저 조회 후 없으면 RTMSDataSvcAptRent API 호출.
    """
    # 1) 전월세 DB 초기화
    init_rent_db()

    current_year = datetime.datetime.now().year
    years_count = max(1, min(3, int(years_count)))
    years = [current_year - i for i in range(years_count)]

    current_month_now = datetime.datetime.now().month

    all_items = []

    for year in years:
        #url = "https://apis.data.go.kr/1613000/RTMSDataSvcAptRent/getRTMSDataSvcAptRent"
        url = "http://apis.data.go.kr/1613000/RTMSDataSvcAptRent/getRTMSDataSvcAptRent"
        service_key = "B2BtWbuZVFz/EJoLsrDa6corOwSR4SsGwjBKzK2WJQ3JVwRMIUoXOGY3BHXrxZq78nP+ECsW5wB4TEwbgxS2PA=="

        params = {
            "serviceKey": service_key,
            "LAWD_CD": lawd_cd,
            "DEAL_YMD": f"{year}01",
            "pageNo": 1,
            "numOfRows": 1000
        }

        year_items = []

        current_month = 12 if year < current_year else current_month_now

        for month in range(1, current_month + 1):
            params_month = dict(params)

            # 1) DB 먼저 조회
            month_items = read_rent_db(
                lawd_cd=lawd_cd,
                umd_nm=umd_nm,
                apt_nm=apt_nm,
                dealYear=str(year),
                dealMonth=str(month)
            )

            if month_items:
                print(f"[APT RENT] {year}년 {month}월: DB에서 {len(month_items)}건 조회됨")

                year_items.extend(month_items)
                all_items.extend(month_items)

            else:
                print(f"[APT RENT] {year}년 {month:02d}월: DB 데이터 없음 → API 요청")

                month_items = fetch_apt_rent_month(
                    url=url,
                    params=params_month,
                    lawd_cd=lawd_cd,
                    lawd_nm=lawd_nm,
                    umd_nm=umd_nm,
                    apt_nm=apt_nm,
                    year=year,
                    month=month,
                    verify=verify
                )

                if month_items:
                    insert_rent_items(month_items, lawd_cd)

                year_items.extend(month_items)
                all_items.extend(month_items)

        print_apt_rent_table(year_items, lawd_cd, year, "전체")
        print(f"\n[APT RENT {year}] 총 누적 건수: {len(year_items)}\n")

    return all_items


def print_apt_rent_table(items: list, lawd_cd: str, year: int, month_str: str) -> None:
    """
    아파트 전월세 결과 콘솔 출력.
    """
    print(f"\n=== {year}년 {month_str} 아파트 전월세 내역 ===")
    print(
        f"{'순번':<8}"
        f"{'법정코드':<12}"
        f"{'거래년도':<10}"
        f"{'거래월':<8}"
        f"{'거래일':<8}"
        f"{'읍면동':<14}"
        f"{'아파트명':<24}"
        f"{'지번':<12}"
        f"{'전용면적':<12}"
        f"{'층':<8}"
        f"{'보증금':<14}"
        f"{'월세':<10}"
        f"{'계약기간':<16}"
        f"{'계약구분':<12}"
        f"{'갱신권사용':<12}"
        f"{'이전보증금':<14}"
        f"{'이전월세':<12}"
        f"{'lat':<12}"
        f"{'lon':<12}"
    )
    print("=" * 220)

    for index, item in enumerate(items, 1):
        print(
            f"{str(index):<8}"
            f"{lawd_cd:<12}"
            f"{str(item.get('dealYear', '') or ''):<10}"
            f"{str(item.get('dealMonth', '') or ''):<8}"
            f"{str(item.get('dealDay', '') or ''):<8}"
            f"{str(item.get('umdNm', '') or ''):<14}"
            f"{str(item.get('aptNm', '') or ''):<24}"
            f"{str(item.get('jibun', '') or ''):<12}"
            f"{str(item.get('excluUseAr', '') or ''):<12}"
            f"{str(item.get('floor', '') or ''):<8}"
            f"{str(item.get('deposit', '') or ''):<14}"
            f"{str(item.get('monthlyRent', '') or ''):<10}"
            f"{str(item.get('contractTerm', '') or ''):<16}"
            f"{str(item.get('contractType', '') or ''):<12}"
            f"{str(item.get('useRRRight', '') or ''):<12}"
            f"{str(item.get('preDeposit', '') or ''):<14}"
            f"{str(item.get('preMonthlyRent', '') or ''):<12}"
            f"{str(item.get('lat', '') or ''):<12}"
            f"{str(item.get('lon', '') or ''):<12}"
        )


def apt_rent_items_to_json(items: list, lawd_cd: str) -> list:
    """
    run_apt_rent() 결과를 JSON 리스트로 변환.
    rent 테이블 구조와 동일하게 맞춤.
    """
    def s(v):
        if v is None:
            return ""
        v = str(v).strip()
        return "" if v.lower() == "null" else v

    json_records = []

    for item in items:
        rec = OrderedDict([
            ("lawd_cd",          s(lawd_cd)),
            ("sggCd",            s(item.get("sggCd", ""))),
            ("umdNm",            s(item.get("umdNm", ""))),
            ("aptNm",            s(item.get("aptNm", ""))),
            ("jibun",            s(item.get("jibun", ""))),
            ("excluUseAr",       s(item.get("excluUseAr", ""))),
            ("dealYear",         s(item.get("dealYear", ""))),
            ("dealMonth",        s(item.get("dealMonth", ""))),
            ("dealDay",          s(item.get("dealDay", ""))),
            ("deposit",          s(item.get("deposit", ""))),
            ("monthlyRent",      s(item.get("monthlyRent", ""))),
            ("floor",            s(item.get("floor", ""))),
            ("buildYear",        s(item.get("buildYear", ""))),
            ("contractTerm",     s(item.get("contractTerm", ""))),
            ("contractType",     s(item.get("contractType", ""))),
            ("useRRRight",       s(item.get("useRRRight", ""))),
            ("roadnm",           s(item.get("roadnm", ""))),
            ("roadnmsggcd",      s(item.get("roadnmsggcd", ""))),
            ("roadnmcd",         s(item.get("roadnmcd", ""))),
            ("roadnmseq",        s(item.get("roadnmseq", ""))),
            ("roadnmbcd",        s(item.get("roadnmbcd", ""))),
            ("roadnmbonbun",     s(item.get("roadnmbonbun", ""))),
            ("roadnmbubun",      s(item.get("roadnmbubun", ""))),
            ("aptSeq",           s(item.get("aptSeq", ""))),
            ("preDeposit",       s(item.get("preDeposit", ""))),
            ("preMonthlyRent",   s(item.get("preMonthlyRent", ""))),
            ("lat",              s(item.get("lat", ""))),
            ("lon",              s(item.get("lon", ""))),
        ])

        json_records.append(rec)

    return json_records



# ==============================
# main — 테스트 실행
# ==============================
if __name__ == "__main__":
    print("\n########## APT RENT(아파트 전월세) ##########")

    lawd_cd = "41570"  # 11110: 서울시 종로구 창신동, 41570-00000: 경기도 김포시 운양동, 4148025326:경기도 파주시 파주읍 파주리
    # 3) 코드로 단건 조회
    res = get_lawd_by_code(lawd_cd + "00000")
    print("[READ]", res)
    lawd_nm = res["lawd_name"]  # 경기도 김포시
    # 읍,면,동 개념으로 파주읍 파주리 경우는 목록은 파주읍 파주리, 붕원리등 나오나 파주읍만 드간다(네이버 부동산 검색기준임).
    umd_nm = "운양동"  # 읍면동(창신동,숭인동, 종로1가, 운양동, 파주읍 등)

    print(f"[main start.] lawd_cd : {lawd_cd} lawd_nm : {lawd_nm} umd_nm : {umd_nm}")

    # === 상가 테스트 ===
    # 1) DB 초기화(테이블 생성)
    # init_sanga_db()

    years_count = 2  # 최근 2개년

    #
    rent_items = run_apt_rent(
        lawd_cd=lawd_cd,
        lawd_nm=lawd_nm,
        umd_nm=umd_nm,
        apt_nm="",
        years_count=years_count,
        verify=False
    )

    rent_json_records = apt_rent_items_to_json(rent_items, lawd_cd)

    # 필요할 때만 JSON 출력
    # print(json.dumps(rent_json_records, ensure_ascii=False, indent=2))

    print(f"\n[아파트 전월세 총 누적 건수: {len(rent_items)}]\n")
