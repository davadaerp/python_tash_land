# -*- coding: utf-8 -*-
import os
import time
from typing import Optional

import requests
import xmltodict
import datetime
import json
from collections import OrderedDict

from pubdata.public_land_lawd_code_db_utils import get_lawd_by_codes, update_land_batch_yn_single, \
    update_land_batch_yn_multi
from pubdata.public_land_apt_db_utils import init_apt_db, read_apt_db, insert_apt_items
from pubdata.public_land_sanga_db_utils import init_sanga_db, insert_sanga_items, read_sanga_db
from pubdata.public_land_villa_db_utils import init_villa_db, read_villa_db, insert_villa_items

# 👇 지오코딩된 건수 글로벌 카운터 (추가)
GEOCODED_COUNT = 0

# ==============================
# 아파트/빌라/상가/비주거 월검색 API
def fetch_land_month(url: str, params: dict, lawd_cd: str, lawd_nm: str, umd_nm: str, year: int, month: int, verify: bool = False):
    """상가/비주거 월별 조회 (XML -> dict)"""
    month_str = f"{month:02d}"
    params["DEAL_YMD"] = f"{year}{month_str}"
    print("fetch_land_month 조회:", lawd_cd, lawd_nm, umd_nm, year, month, month_str)

    response = requests.get(url, params=params, verify=verify)
    if response.status_code != 200:
        print(f"{year}년 {month_str}월: API 요청 실패: {response.status_code}, 응답 내용: {response.text}")
        return []

    try:
        response_dict = xmltodict.parse(response.text)
        response_data = response_dict.get('response', {})
        body = response_data.get('body', {})
        items = body.get('items', {})

        if not items or not isinstance(items, dict) or 'item' not in items:
            print(f"{year}년 {month_str}월: 검색된 데이터가 없습니다.")
            return []

        items = items['item']
        if isinstance(items, dict):
            items = [items]

        items_sorted = sorted(
            items,
            key=lambda x: (x.get('dealYear', ''), x.get('dealMonth', ''), x.get('dealDay', ''))
        )

        # 👉 특정 시군구명(sgg_nm)만 필터링
        # 읍면동 공백 대비(트림)
        umd_nm = (umd_nm or "").strip()
        filtered_items = [it for it in items_sorted if it.get("umdNm", "") == umd_nm]

        # # 🟢 수정된 부분 시작: 시군구명 필터링 및 지번에 '*'가 없는 항목만 필터링(차후 실거래금액 구할때 없애면 안될듯)
        # filtered_items = []
        # for it in items_sorted:
        #     # 1. 시군구명(umdNm) 필터링
        #     if it.get("umdNm", "") == umd_nm:
        #         jibun = it.get("jibun", "")
        #         # 2. 지번(`jibun`)에 '*'가 포함되지 않은 항목만 포함
        #         if "*" not in jibun:
        #             filtered_items.append(it)
        #         else:
        #             # '*'가 포함된 항목은 건너뜁니다.
        #             print(f"INFO: Jibun contains '*', skipping item: {lawd_nm} {it.get('umdNm', '')} {jibun}")
        # # 🟢 수정된 부분 끝

        # 각 item에 위도/경도 추가
        for it in filtered_items:
            it["sggNm"] = lawd_nm   # 시군구명(서울시 종로구)
            umdNm = it.get("umdNm", "")
            jibun = it.get("jibun", "")

            # --- 수정된 부분 시작: 지번에 '*' 포함 시 geocode 생략 및 0.0 처리 ---
            if "*" in jibun:
                print(f"WARNING: Jibun contains '*', skipping geocoding for: {lawd_nm} {umdNm} {jibun}")
                it["lat"] = "0.0"
                it["lon"] = "0.0"
            else:
                # 전체 주소 조합 및 geocoding
                address = f"{lawd_nm} {umdNm} {jibun}"
                # geo = geocode_vworld(address)
                geo = geocode(address)
                it["lat"] = str(geo["lat"])
                it["lon"] = str(geo["lng"])
                print("Geocoding address:", address, "->", geo)

                # 👇 지오코딩이 수행된 건만 글로벌 카운트 (추가)
                global GEOCODED_COUNT
                GEOCODED_COUNT += 1
            # --- 수정된 부분 끝 ---

        return filtered_items

    except Exception as e:
        print(f"{year}년 {month_str}월: XML 파싱 오류: {e}")
        return []


# // vWorld 지오코딩 래퍼-api호출은 tash서버에서 처리함
def geocode_vworld(address: str) -> dict:
    """
    tash 서버에 구축된 vWorld 지오코딩 래퍼 API 호출
    address: 문자열 주소
    return: {"lat": float, "lng": float}
    """
    url = "https://erp-dev.bacchuserp.com/api/geocode"
    params = {"address": address}

    try:
        res = requests.get(url, params=params, timeout=5)
        if res.status_code != 200:
            print("Network response not ok", res.status_code)
            return {"lat": 0.0, "lng": 0.0}

        data = res.json()
        status = data.get("response", {}).get("status")
        point  = data.get("response", {}).get("result", {}).get("point")

        if status != "OK" or not point or point.get("x") is None or point.get("y") is None:
            print("Geocode failed:", data)
            return {"lat": 0.0, "lng": 0.0}

        return {
            "lat": float(point.get("y") or 0.0),
            "lng": float(point.get("x") or 0.0)
        }
    except Exception as e:
        print("geocode_vworld error:", e)
        return {"lat": 0.0, "lng": 0.0}

# 차후 서버상에서는 아래로 수정함
def geocode(address: str) -> dict:
    MAP_API_KEY = "644F5AF8-9BF1-39DE-A097-22CACA23352F"
    params = {
        "service":"address",
        "request":"getcoord",
        "format":"json",
        "crs":"epsg:4326",
        "type":"parcel",
        "address":address,
        "key":MAP_API_KEY
    }
    try:
        r = requests.get("https://api.vworld.kr/req/address", params=params, timeout=5)
        data = r.json() # jsonify 처리 체크
        #
        status = data.get("response", {}).get("status")
        point  = data.get("response", {}).get("result", {}).get("point")

        if status != "OK" or not point or point.get("x") is None or point.get("y") is None:
            print("Geocode failed:", data)
            return {"lat": 0.0, "lng": 0.0}

        return {
            "lat": float(point.get("y") or 0.0),
            "lng": float(point.get("x") or 0.0)
        }
    except Exception as e:
        print("geocode_vworld error:", e)
        return {"lat": 0.0, "lng": 0.0}


# ==============================
# 국토부실거래 상가 (SANGA) 전체 실행
# ==============================
def run_sanga(lawd_cd: str, lawd_nm:str, umd_nm: str,  verify: bool = False):
    # 1) DB 초기화(테이블 생성)
    init_sanga_db()

    # 현재 연도 기준 최근 2개년
    current_year = datetime.datetime.now().year
    years = [current_year, current_year - 1]
    current_month = datetime.datetime.now().month # 현재 월
    #
    all_items = []
    for year in years:
        """상가/비주거 1개년 전체 조회"""
        # url = "https://apis.data.go.kr/1613000/RTMSDataSvcNrgTrade/getRTMSDataSvcNrgTrade"
        # service_key = "B2BtWbuZVFz/EJoLsrDa6corOwSR4SsGwjBKzK2WJQ3JVwRMIUoXOGY3BHXrxZq78nP+ECsW5wB4TEwbgxS2PA=="
        url = "http://apis.data.go.kr/1613000/RTMSDataSvcNrgTrade/getRTMSDataSvcNrgTrade"
        service_key = "B2BtWbuZVFz/EJoLsrDa6corOwSR4SsGwjBKzK2WJQ3JVwRMIUoXOGY3BHXrxZq78nP+ECsW5wB4TEwbgxS2PA=="
        params = {
            "serviceKey": service_key,
            "LAWD_CD": lawd_cd,
            "DEAL_YMD": f"{year}01",
            "pageNo": 1,
            "numOfRows": 1000
        }
        year_items = []
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
                print(f"{year}년 {month:02d}월: DB 데이터 없음 → API 요청(SANGA)")
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
def run_villa(lawd_cd: str, lawd_nm:str, umd_nm: str,  verify: bool = False):
    # 1) DB 초기화(테이블 생성)
    init_villa_db()

    # 현재 연도 기준 최근 2개년
    current_year = datetime.datetime.now().year
    years = [current_year, current_year - 1]
    current_month = datetime.datetime.now().month  # 현재 월
    #
    all_items = []
    for year in years:
        # """상가/비주거 1개년 전체 조회"""
        # url = "http://apis.data.go.kr/1613000/RTMSDataSvcNrgTrade/getRTMSDataSvcNrgTrade"
        # service_key = "B2BtWbuZVFz/EJoLsrDa6corOwSR4SsGwjBKzK2WJQ3JVwRMIUoXOGY3BHXrxZq78nP+ECsW5wB4TEwbgxS2PA=="
        """빌라 1개년 전체 조회"""
        url = "http://apis.data.go.kr/1613000/RTMSDataSvcRHTrade/getRTMSDataSvcRHTrade"
        service_key = "B2BtWbuZVFz/EJoLsrDa6corOwSR4SsGwjBKzK2WJQ3JVwRMIUoXOGY3BHXrxZq78nP+ECsW5wB4TEwbgxS2PA=="
        params = {
            "serviceKey": service_key,
            "LAWD_CD": lawd_cd,
            "DEAL_YMD": f"{year}01",
            "pageNo": 1,
            "numOfRows": 1000
        }
        year_items = []
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
                print(f"{year}년 {month:02d}월: DB 데이터 없음 → API 요청(VILLA)")
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
def run_apt(lawd_cd: str, lawd_nm:str, umd_nm: str, apt_nm:str, verify: bool = False):
    # 1) DB 초기화(테이블 생성)
    init_apt_db()

    # 현재 연도 기준 최근 2개년
    current_year = datetime.datetime.now().year
    years = [current_year, current_year - 1]
    current_month = datetime.datetime.now().month  # 현재 월
    #
    all_items = []
    for year in years:
        # """아파트 1개년 전체 조회"""
        # url = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade"
        # service_key = "B2BtWbuZVFz/EJoLsrDa6corOwSR4SsGwjBKzK2WJQ3JVwRMIUoXOGY3BHXrxZq78nP+ECsW5wB4TEwbgxS2PA=="
        """아파트 1개년 전체 조회"""
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
                print(f"{year}년 {month:02d}월: DB 데이터 없음 → API 요청(APT)")
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
# 법정동명에서 시군구명(sgg_nm)과 읍/면/동/리/가 추출 유틸리티
def extract_eup_myeon_dong(lawd_name: str) -> Optional[tuple[str, str]]:
    """
    법정동명 문자열(예: '서울특별시 종로구 청운동')에서
    시군구명(sgg_nm)과 읍/면/동/리/가(umd_nm) 부분을 추출합니다.

    Args:
        lawd_name: 법정동명 문자열.

    Returns:
        추출된 (시군구명, 읍면동명) 튜플 (예: ('서울특별시 종로구', '청운동')),
        또는 찾지 못하면 None.
    """
    if not lawd_name:
        return None

    # 일반적으로 사용되는 말단 행정구역 단위
    UNITS = ['읍', '면', '동', '리', '가']

    # 공백을 기준으로 나눕니다.
    parts = lawd_name.split()

    # 마지막 파트부터 역순으로 탐색하여 읍면동명을 찾습니다.
    umd_nm = None
    umd_index = -1  # 읍면동명이 위치한 인덱스

    for i in reversed(range(len(parts))):
        part = parts[i]
        # 파트의 마지막 글자가 '읍', '면', '동', '리', '가' 중 하나인지 확인
        if len(part) > 1 and part[-1] in UNITS:
            umd_nm = part
            umd_index = i
            break

    if umd_nm is None:
        return None  # 읍면동명 찾기 실패

    # 읍면동명 앞까지의 모든 파트를 시군구명으로 간주합니다.
    # 예: ['서울특별시', '종로구', '청운동'] -> '청운동'은 인덱스 2. sgg_parts는 [0, 1]
    sgg_parts = parts[:umd_index]
    sgg_nm = " ".join(sgg_parts)

    # 시군구명은 공백이 아니어야 합니다.
    if not sgg_nm:
        return None

    return sgg_nm, umd_nm


# ==============================
# 헬퍼 함수: 배치 로그에서 최종 처리 일자 읽기 (lawd_cd 제거)
# ==============================
# ==============================
# 헬퍼 함수: 배치 로그에서 최종 처리 일자 읽기 (lawd_cd 제거)
# ==============================
def get_last_batch_date(batch_log_file: str) -> Optional[datetime.date]:
    """
    배치 로그 파일 (덮어쓰기 방식으로 저장된)에서 기록된 가장 최근의 배치 제한 일자를 읽습니다.
    로그 형식: 일시(YYYY-MM-DD HH:MM:SS), OVER_LIMIT, 누적건수
    """
    try:
        if not os.path.exists(batch_log_file):
            return None

        with open(batch_log_file, "r", encoding="utf-8") as f:
            # 💡 수정: 파일이 덮어쓰기로 저장되므로, 첫 번째 라인(가장 최근 기록)만 읽습니다.
            first_line = f.readline().strip()
            if not first_line:
                return None

            parts = first_line.split(',')
            # OVER_LIMIT 태그 확인
            if len(parts) >= 3 and parts[1] == 'OVER_LIMIT':
                # 일시 (YYYY-MM-DD HH:MM:SS)에서 날짜 부분만 추출
                date_part = parts[0].split(' ')[0]
                last_date = datetime.datetime.strptime(date_part, "%Y-%m-%d").date()
                return last_date
            return None # OVER_LIMIT 태그가 없는 경우
    except Exception as e:
        print(f"로그 파일 읽기 중 오류 발생: {e}")
        return None


# ==============================
# 헬퍼 함수: 누적 건수 초과 시 로그 기록 (lawd_cd 제거, 파일에 lawd_cd는 포함)
# ==============================
# ==============================
# 헬퍼 함수: 누적 건수 초과 시 로그 기록 (lawd_cd 제거, 파일에 lawd_cd는 포함)
# ==============================
def log_batch_over_limit_date(cumulative_count: int, gecode_count: int, max_limit: int, batch_log_file: str):
    """
    gecode변환 누적 건수 제한 초과 시 현재 일자를 파일에 기록하고, 중단 신호를 반환합니다.
    (함수 호출 시 lawd_cd를 인자로 받아 파일에 기록합니다.)
    """
    if gecode_count > max_limit:
        current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            # 💡 수정: 파일 모드를 "a" (추가)에서 "w" (쓰기/덮어쓰기)로 변경
            with open(batch_log_file, "w", encoding="utf-8") as f:
                # 로그 형식: 일시(YYYY-MM-DD HH:MM:SS), OVER_LIMIT, 누적건수
                # (lawd_cd는 제거됨)
                f.write(f"{current_datetime},OVER_LIMIT,총건수:{cumulative_count},주소변환건수:{gecode_count}\n")
            print(f"⚠️ [주소변환 누적 건수({gecode_count})가 {max_limit}건을 초과하여 처리를 중단하고 {batch_log_file}에 기록되었습니다.")
            return True  # 중단 필요
        except Exception as e:
            print(f"❌ 로그 파일 저장 중 오류 발생: {e}")
            return True  # 오류 발생 시에도 안전하게 중단

    return False  # 계속 진행


#
# ==============================
# 배치 본처리 함수 (기존 main 루프 분리)
# ==============================
def _process_land_batch(MAX_DAILY_COUNT: int = 25000, batch_log_file: str = "batch_land_lawd.txt") -> None:
    import datetime, time

    # 실행 전 카운터 초기화
    global GEOCODED_COUNT
    GEOCODED_COUNT = 0

    # 1) 전체 법정동 코드 조회
    all_lawd_records = get_lawd_by_codes()
    print(f"[필터링] 총 법정동 레코드 건수: {len(all_lawd_records)}")

    # 처리 상태 플래그 초기화
    cumulative_count = 0
    should_stop_batch = False

    # 2) 'batch_apt_yn'/'batch_villa_yn'/'batch_sanga_yn' 이 'N'인 것만 처리
    for record in all_lawd_records:
        full_lawd_cd = record["lawd_cd"]  # 10자리
        full_lawd_nm = record["lawd_name"]
        batch_apt_yn = record.get("batch_apt_yn")
        batch_villa_yn = record.get("batch_villa_yn")
        batch_sanga_yn = record.get("batch_sanga_yn")

        print("record:", record)

        # 읍/면/동 추출
        result = extract_eup_myeon_dong(full_lawd_nm)
        if result is None:
            print(f"읍/면/동명 추출 실패: 법정동명='{full_lawd_nm}'")
            continue

        # 시군구/읍면동명
        lawd_cd = full_lawd_cd[:5]
        lawd_nm, umd_nm = result

        print(f"\n--- 법정동 처리 시작: {lawd_cd} ({lawd_nm}, {umd_nm}) ---")

        # 이미 모두 처리(Y/Y/Y)면 스킵
        if not (batch_apt_yn == 'N' or batch_villa_yn == 'N' or batch_sanga_yn == 'N'):
            continue

        # ✅ [추가 로직] lawd_nm 안에 '면' 또는 '읍'이 있으면
        #    APT / SANGA / VILLA 를 모두 'Y'로만 업데이트하고 스킵
        if ('면' in lawd_nm) or ('읍' in lawd_nm) or ('면' in umd_nm) or ('읍' in umd_nm):
            print(f"⚠️ 면/읍 지역 스킵: {lawd_cd} ({lawd_nm}, {umd_nm}) -> 배치 상태만 Y로 업데이트")

            update_land_batch_yn_multi("4374532000", apt="Y", villa="Y", sanga="Y")

            # 실제 run_apt / run_sanga / run_villa 는 수행하지 않고 다음 레코드로
            continue

        # 2-1) APT
        if not should_stop_batch and batch_apt_yn == 'N':
            try:
                apt_items = run_apt(lawd_cd, lawd_nm, umd_nm, apt_nm="", verify=False)
                apt_count = len(apt_items)
                cumulative_count += apt_count
                print(f"[APT] {lawd_nm} ({umd_nm}) 처리 건수: {apt_count} 건 (누적: {cumulative_count})")

                update_land_batch_yn_single(full_lawd_cd, "APT", "Y")

                should_stop_batch = log_batch_over_limit_date(cumulative_count, GEOCODED_COUNT, MAX_DAILY_COUNT, batch_log_file)
                if should_stop_batch:
                    print(f"⚠️ [APT] 주소변환 누적 건수({MAX_DAILY_COUNT}) 제한으로 인해 {lawd_cd} ({lawd_nm})의 추가 처리를 중단합니다.")
                    break
            except Exception as e:
                print(f"❌ [APT] 처리 중 오류 발생: {e}")
                should_stop_batch = True
                update_land_batch_yn_single(full_lawd_cd, "APT", "N")

        time.sleep(0.5)

        # 2-2) SANGA
        if not should_stop_batch and batch_sanga_yn == 'N':
            try:
                sanga_items = run_sanga(lawd_cd, lawd_nm, umd_nm, verify=False)
                sanga_count = len(sanga_items)
                cumulative_count += sanga_count
                print(f"[SANGA] {lawd_nm} ({umd_nm}) 처리 건수: {sanga_count} 건 (누적: {cumulative_count})")

                update_land_batch_yn_single(full_lawd_cd, "SANGA", "Y")

                should_stop_batch = log_batch_over_limit_date(cumulative_count, GEOCODED_COUNT, MAX_DAILY_COUNT, batch_log_file)
                if should_stop_batch:
                    print(f"⚠️ [SANGA] 주소변환 누적 건수({MAX_DAILY_COUNT}) 제한으로 인해 {lawd_cd} ({lawd_nm})의 추가 처리를 중단합니다.")
                    break
            except Exception as e:
                print(f"❌ [SANGA] 처리 중 오류 발생: {e}")
                should_stop_batch = True
                update_land_batch_yn_single(full_lawd_cd, "SANGA", "N")

        time.sleep(0.5)

        # 2-3) VILLA
        if not should_stop_batch and batch_villa_yn == 'N':
            try:
                villa_items = run_villa(lawd_cd, lawd_nm, umd_nm, verify=False)
                villa_count = len(villa_items)
                cumulative_count += villa_count
                print(f"[VILLA] {lawd_nm} ({umd_nm}) 처리 건수: {villa_count} 건 (누적: {cumulative_count})")

                update_land_batch_yn_single(full_lawd_cd, "VILLA", "Y")

                should_stop_batch = log_batch_over_limit_date(cumulative_count, GEOCODED_COUNT, MAX_DAILY_COUNT, batch_log_file)
                if should_stop_batch:
                    print(f"⚠️ [VILLA] 주소변환 누적 건수({MAX_DAILY_COUNT}) 제한으로 인해 {lawd_cd} ({lawd_nm})의 추가 처리를 중단합니다.")
                    break
            except Exception as e:
                print(f"❌ [VILLA] 처리 중 오류 발생: {e}")
                should_stop_batch = True
                update_land_batch_yn_single(full_lawd_cd, "VILLA", "N")

        # 4) 결과 출력
        if not should_stop_batch:
            print(f"✅ {lawd_cd} ({lawd_nm})의 배치 처리가 성공적으로 완료되었습니다 (총 {cumulative_count}건).")
        elif should_stop_batch:
            print(f"⚠️ {lawd_cd} ({lawd_nm})는 누적 건수 제한 또는 오류로 인해 중단되었습니다.")
        else:
            print(f"❌ {lawd_cd} ({lawd_nm})의 일부 배치 처리가 실패했습니다.")

    print(f"\n[총 법정동 레코드 건수: {len(all_lawd_records)}]")
    print(f"배치 처리 정보는 {batch_log_file} 파일을 확인하세요.")


# ==============================
# 하루 1회 실행 보장 래퍼 함수
# ==============================
def run_land_batch_once_per_day(MAX_DAILY_COUNT: int = 25000, batch_log_file: str = "batch_land_lawd.txt") -> bool:
    """
    로그 파일의 최근 OVER_LIMIT 일자를 읽어,
    같은 날짜에는 배치를 재실행하지 않고 건너뜁니다.
    실행했으면 True, 건너뛰었으면 False 반환.
    """
    import datetime

    today_date = datetime.date.today()
    global_last_batch_date = get_last_batch_date(batch_log_file)
    is_ready_for_rebatch = (global_last_batch_date is None) or (today_date > global_last_batch_date)

    if not is_ready_for_rebatch:
        print(f"🔴 글로벌 배치 제한 일자({global_last_batch_date})가 오늘({today_date})과 같거나 이후이므로, 배치 처리를 건너뜁니다.")
        return False

    # 배치 본처리 함수 호출
    _process_land_batch(MAX_DAILY_COUNT=MAX_DAILY_COUNT, batch_log_file=batch_log_file)
    return True


# ==============================
# main — 테스트 실행 (수정된 버전)
# ==============================
if __name__ == "__main__":
    # 일일 최대 처리 건수 설정 (요청 조건: 27000건, 테스트: 1000건)
    MAX_DAILY_COUNT = 29000
    batch_log_file = "batch_land_lawd.txt"

    # 3. 하루 1회 실행 보장 래퍼 함수 호출
    run_land_batch_once_per_day(MAX_DAILY_COUNT, batch_log_file)