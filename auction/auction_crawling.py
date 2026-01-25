import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import time
import re
import json
import os
#
from auction_db_utils import auction_save_to_sqlite
from config import AUCTION_DB_PATH, MAP_API_KEY, VWORLD_URL

# 저장파일명
last_file_name = os.path.join(AUCTION_DB_PATH, "last_auction_date.txt")

# ------------------------------
# 텍스트 파일에서 마지막 날짜를 읽어오는 함수
def get_last_sale_date():
    if os.path.exists(last_file_name):
        with open(last_file_name, "r", encoding="utf-8") as f:
            date_str = f.read().strip()
            if date_str:
                return date_str
    return None

# 마지막 날짜를 텍스트 파일에 저장하는 함수
def save_last_sale_date(date_str):
    with open(last_file_name, "w", encoding="utf-8") as f:
        f.write(date_str)
# ------------------------------

# 스크립트 시작 시 현재 날짜 기준으로 sale_edate를 설정하고,
# 이전에 저장된 마지막 날짜가 있으면 sale_sdate에 할당, 없으면 현재 날짜로 처리
today = datetime.today().strftime("%Y-%m-%d")
last_sale_date = get_last_sale_date()
if last_sale_date:
    sale_sdate = last_sale_date
else:
    sale_sdate = today
    #
sale_edate = today
# ------------------------------

# 저장 방식 선택: "csv" 또는 "sqlite"
SAVE_MODE = "sqlite"  # 원하는 방식으로 변경 가능 (예: "csv")
BATCH_SIZE = 500     # 레코드 1000건마다 저장

# 글로벌 변수 설정
page_list = "100"
data_list = []
saved_count = 0    # 누적 저장 건수
map_api_key = "AIzaSyBzacpsf9Cw3CRRqWXUHbHkRDNbYlaXGCI"    # 구글맴 api_key

# 팝업 닫기 함수
def close_popups(driver):
    #
    try:
        # 광고 배너 닫기 (예: 메인광고 마스크)
        ad_mask = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "mainbannerMask"))
        )
        driver.execute_script("document.getElementById('mainbannerMask').style.display = 'none';")
        print("메인 배너 광고 닫음.")
    except Exception:
        print("메인 배너 광고 없음.")

    try:
        # 광고 배너 닫기
        ad_banner_close = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//*[@onclick=\"div_adBtn('1');\"]"))
        )
        ad_banner_close.click()
        print("광고 배너 팝업 닫음.")
    except Exception:
        print("광고 배너 없음.")

    try:
        # 기타 팝업 닫기 (예: 공지사항, 이벤트 등)
        popup_close_buttons = driver.find_elements(By.CLASS_NAME, "popup_close")
        for btn in popup_close_buttons:
            btn.click()
        print(f"{len(popup_close_buttons)}개의 기타 팝업 닫음.")
    except Exception:
        print("기타 팝업 없음.")

# 로그인처리
def login(driver):
    try:
        login_button = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.XPATH, "//*[@onclick='floating_div(400);']"))
        )
        login_button.click()

        # 로그인 팝업이 표시될 때까지 대기 (팝업의 id는 "FLOATING_CONTENT")
        login_popup = WebDriverWait(driver, 3).until(
            EC.visibility_of_element_located((By.ID, "FLOATING_CONTENT"))
        )

        # 디버깅을 위한 로그인 팝업 HTML 출력
        login_html = login_popup.get_attribute("outerHTML")
        print("로그인 팝업의 HTML:" + login_html)

        username_field = login_popup.find_element(By.NAME, "client_id")
        password_field = login_popup.find_element(By.NAME, "passwd")
        username_field.send_keys("wfight69")
        password_field.send_keys("ahdtpddlta_0")

        submit_button = login_popup.find_element(By.XPATH, ".//a[contains(@onclick, 'login();')]")
        submit_button.click()

        print("로그인 시도 완료.")
    except Exception as e:
        print("로그인 오류:", e)

# 메뉴처리
def menu_search(driver):
    try:
        # ======================================================================
        # "경매검색" 메뉴 클릭 (<a href="/ca/caList.php" ... >경매검색</a> 요소 선택)
        auction_search = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@href='/ca/caList.php' and contains(text(), '경매검색')]"))
        )
        auction_search.click()
        print("경매검색 메뉴 클릭 완료.")

    except Exception as e:
        print("경매검색 메뉴선택 오류:", e)

# 카테고리 선택
def select_categories(driver):

    # ======================================================================
    # [추가] "showCtgrMulti(this)" 버튼 클릭하여 카테고리 선택 창 열기
    category_button = WebDriverWait(driver, 3).until(
        EC.element_to_be_clickable((By.XPATH, "//*[@onclick='showCtgrMulti(this)']"))
    )
    category_button.click()
    print("카테고리 선택 창 열기 완료.")

    # 잠시 대기 (모달/드롭다운이 로드될 시간 확보)
    time.sleep(2)

    # ======================================================================
    # [추가] 매각전부 옵션 선택
    try:
        stat_select = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "stat"))
        )
        select_obj = Select(stat_select)
        select_obj.select_by_value("12")
        print("매각전부 옵션 선택됨.")
        time.sleep(2)
    except Exception as e:
        print("매각전부 옵션 선택 중 오류 발생:", e)

    # # DOM속성을 이용하여 처리함.
    # try:
    #     stat_select = WebDriverWait(driver, 10).until(
    #         EC.presence_of_element_located((By.ID, "stat"))
    #     )
    #     # JavaScript를 사용하여 '매각전부' 옵션 수정(Dom속성 바로제어함)
    #     driver.execute_script("""
    #         let option = [...document.querySelectorAll("#stat option")].find(opt => opt.textContent.includes("매각전부"));
    #         if (option) {
    #             option.removeAttribute("disabled");
    #             option.classList.remove("bg_gray");
    #             option.setAttribute("value", "12");
    #         }
    #     """)
    #     # Select 객체를 사용하여 수정된 옵션 선택
    #     select_obj = Select(stat_select)
    #     select_obj.select_by_value("12")
    #
    #     print("매각전부 옵션 선택됨.")
    #     time.sleep(2)
    # except Exception as e:
    #     print("매각전부 옵션 선택 중 오류 발생:", e)

    # [추가] 매각일자 설정
    try:
        bgnDt = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "bgnDt"))
        )
        endDt = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "endDt"))
        )
        bgnDt.clear()
        bgnDt.send_keys(sale_sdate)
        endDt.clear()
        endDt.send_keys(sale_edate)
        print(f"매각일자 설정 완료: 시작일자 {sale_sdate}, 종료일자 {sale_edate}")
        time.sleep(1)
    except Exception as e:
        print("매각일자 설정 중 오류 발생:", e)
    #
    try:
        categories = ["아파트", "연립주택", "다세대주택", "오피스텔(주거)", "단독주택", "다가구주택", "도시형생활주택", "상가주택"]
        for category in categories:
            checkbox = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH,
                                            f"//*[@id='ulGrpCtgr_10']//span[contains(text(), '{category}')]/preceding-sibling::input[@type='checkbox']"))
            )
            if not checkbox.is_selected():
                checkbox.click()
                print(f"'{category}' 체크박스 선택됨.")
    except Exception as e:
        print("카테고리 선택 오류:", e)

    # [추가] <ul id="ulGrpCtgr_20"> 내에서 "근린생활시설"과 "근린상가" 항목 체크
    for category in ["근린생활시설", "근린상가", "숙박시설", "업무시설", "공장", "창고"]:
        try:
            checkbox = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable(
                    (By.XPATH, f"//*[@id='ulGrpCtgr_20']//span[contains(text(), '{category}')]/preceding-sibling::input[@type='checkbox']")
                )
            )
            if not checkbox.is_selected():
                checkbox.click()
                print(f"'{category}' 체크박스 선택됨.")
        except Exception as e:
            print(f"'{category}' 체크박스 선택 중 오류 발생:", e)

    # ======================================================================
    # 첫번째 검색으로 페이지에 총건수를 가져오기 위함.
    driver.execute_script("srchClick();")
    print("srchClick() 검색함수 실행 완료.")

    # 결과가 로드될 때까지 대기 (#lsTbody 요소가 로드되길 기다림)
    tbody = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#lsTbody"))
    )
    # 형식적경매 결과는 출력하지 않고 잠시 대기만 함
    time.sleep(3)

    # ======================================================================
    # [추가] 목록수를 100으로 설정 (select 태그 처리)
    try:
        data_size_select = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "dataSize_s"))
        )
       #driver.execute_script("document.getElementById('dataSize_s').onchange = null;")  # onchange 이벤트 비활성화
        select_obj = Select(data_size_select)
        select_obj.select_by_value(page_list)
        print(f"목록수가 {page_list}으로 설정되었습니다.")
        # onchange 이벤트 실행 시간 고려하여 잠시 대기
        time.sleep(1)
    except Exception as e:
        print("목록수 설정 중 오류 발생:", e)

# ======================================================================
# 총건수 가져오기 함수
def get_total_count(driver):
    try:
        # 총건수 요소 찾기
        total_count_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "totalCnt"))
        )
        total_count = total_count_element.text.strip().replace(",", "")  # 숫자 형식 정리
        print(f"🔹 총 검색된 물건 수: {total_count} 건")
        return int(total_count)
    except Exception as e:
        print("총건수 가져오기 오류:", e)
        return 0

# ======================================================================
# 레코드 데이타 처리
# 결과가 로드될 때까지 대기 (#lsTbody 요소가 로드되길 기다림)
def record_parsing_list(driver, current_page):
    global saved_count, data_list
    #
    # 결과가 로드될 때까지 대기 (#lsTbody 요소가 로드되길 기다림)
    tbody = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#lsTbody"))
    )
    # tbody 안의 모든 tr 요소 선택
    rows = tbody.find_elements(By.TAG_NAME, "tr")
    for idx, row in enumerate(rows, start=1):
        row_text = row.text.strip()
        extract_info(row_text, idx)

        # 1000건마다 저장 처리
        if len(data_list) >= BATCH_SIZE:
            print(f"저장 전 현재까지 저장 건수: {saved_count + len(data_list)} 건, 이번 배치: {len(data_list)} 건")
            auction_save_to_sqlite(data_list)
            saved_count += len(data_list)
            data_list.clear()
            time.sleep(1)

    total_parsed = (current_page - 1) * int(page_list) + idx
    print(f"📄 현재 페이지: {current_page}, 현재목록 수: {idx}, 현재까지 읽은 목록 수: {total_parsed}")

# ======================================================================
# 페이징 이동 및 데이터 처리
def navigate_pages(driver, total_records):
    total_pages = (total_records // int(page_list)) + (1 if total_records % int(page_list) > 0 else 0)
    visited_pages = set()  # 방문한 페이지 번호 저장

    for page_no in range(1, total_pages + 1):
        try:
            print(f"\n📌 {page_no}/{total_pages} 페이지 이동 중...")

            # 이미 방문한 페이지는 스킵
            if str(page_no) in visited_pages:
                print(f"✅ {page_no} 페이지는 이미 방문하여 스킵.")
                continue
            visited_pages.add(str(page_no))

            # JavaScript로 페이지 이동 실행
            driver.execute_script(f"srchList({page_no}); chkEachlist();")
            time.sleep(5)  # 페이지 로딩 대기

            # 레코드 파싱 및 데이터 저장
            record_parsing_list(driver, page_no)

        except Exception as e:
            print("❌ 페이지 이동 중 오류 발생 또는 마지막 페이지 도달:", e)
            break

# 위.경도 가져오기..
# 발급받은 API Key
def get_lat_lng(address: str) -> tuple[float, float]:
    """
    vWorld 지오코딩 API를 호출해 도로명 주소의 위도/경도 좌표를 반환합니다.
    :param address: 조회할 도로명 주소 문자열
    :return: (latitude, longitude)
    :raises Exception: API 오류 또는 좌표 미발견 시
    """
    #url = "https://api.vworld.kr/req/address"
    url = VWORLD_URL
    params = {
        "service": "address",
        "request": "getcoord",  # 좌표 변환 요청
        "format": "json",  # JSON 응답
        "crs": "epsg:4326",  # WGS84 좌표계
        "type": "parcel",  # road: 도로명, parcel: 지번
        "address": address,
        "key": MAP_API_KEY
    }

    resp = requests.get(url, params=params, timeout=5)
    resp.raise_for_status()

    data = resp.json()
    # 응답 구조: data["response"]["status"] == "OK" 인지 확인
    if data.get("response", {}).get("status") != "OK":
        # raise Exception(f"API error: {data.get('response', {}).get('error', 'Unknown error')}")
        return 0.0, 0.0

    # 좌표는 data["response"]["result"]["point"]["y"], ["x"]
    result = data["response"]["result"]
    point = result.get("point")
    if not point or "x" not in point or "y" not in point:
        # raise Exception("좌표를 찾을 수 없습니다.")
        return 0.0, 0.0

    lat = float(point["y"])
    lng = float(point["x"])
    return lat, lng


# 동,층정보 가져오기
def extract_building_floor(address):
    # 동 앞 숫자 추출
    building_match = re.search(r'(\d+)\s?동', address)
    building = building_match.group(1) if building_match else '1'

    # 층 앞 숫자 추출
    floor_match = re.search(r'(\d+)\s?층', address)
    floor = floor_match.group(1) if floor_match else '1'

    # 단지명 처리
    complex_match = re.search(r'\(([^)]+)\)', address)  # 괄호 안의 내용 추출
    if complex_match:
        complex_data = complex_match.group(1)
        if "," in complex_data:
            dangi_name = complex_data.split(",")[-1].strip()  # 쉼표 기준으로 마지막 값
        else:
            dangi_name = complex_data.strip()
    else:
        dangi_name = ""

    return building, floor, dangi_name

# 주소로 시군구 데이타 파싱및 분석
def extract_info(row_text, idx):
    try:
        lines = row_text.split('\n')

        # 기본 정보 추출
        category = lines[0]  # 구분 (예: 아파트)
        case_number = lines[1]  # 사건번호
        address1 = lines[2]  # 주소1
        address2 = lines[3] if lines[3].startswith('(') else ''  # 주소2 (괄호 포함)

        # 주소 세부 정보 추출 (지역, 시군구, 법정동)
        address_parts = address1.split()

        region = address_parts[0] if len(address_parts) > 0 else ''
        # city_district = address_parts[1] if len(address_parts) > 1 else ''
        # legal_dong = address_parts[2] if len(address_parts) > 2 else ''

        # 면적 정보 추출
        area_match = re.search(r'건물\s([\d\.]+)㎡\(([\d\.]+)평\),\s대지권\s([\d\.]+)㎡\(([\d\.]+)평\)', row_text)
        if area_match:
            building_m2, building_py, land_m2, land_py = area_match.groups()
            area_py = float(building_py)
        else:
            building_m2 = building_py = land_m2 = land_py = ''
            area_py = 0

        # 금액 정보 추출
        try:
            idx_price_start = next(
                i for i, line in enumerate(lines) if ("토지" in line or "건물" in line) and "매각" in line) + 1
            appraisal_price = int(lines[idx_price_start].replace(',', ''))  # 감정금액
            min_price = int(lines[idx_price_start + 1].replace(',', ''))  # 최저금액
            sale_price = int(lines[idx_price_start + 2].replace(',', ''))  # 매각금액
        except Exception:
            appraisal_price = min_price = sale_price = 0

        # 비율 정보 추출
        percent_match = re.findall(r'\((\d+)%\)', row_text)
        min_percent = percent_match[0] if len(percent_match) > 0 else ''
        sale_percent = percent_match[1] if len(percent_match) > 1 else ''

        # 매각일자 추출 (yyyy-mm-dd 형식 변환)
        date_match = re.search(r'(\d{2}\.\d{2}\.\d{2})', row_text)
        if date_match:
            raw_date = date_match.group(1)
            sales_date = f"20{raw_date[:2]}-{raw_date[3:5]}-{raw_date[6:]}"
        else:
            sales_date = ''

        # 기타 정보 추출
        extra_info = ', '.join([line for line in lines if '계' in line or '토지' in line or '건물' in line or '임차인' in line])

        # 평단가 계산
        if area_py != 0:
            pydanga_appraisal = int(appraisal_price / (area_py * 10000))
            pydanga_min = int(min_price / (area_py * 10000))
            pydanga_sale = int(sale_price / (area_py * 10000))
        else:
            pydanga_appraisal = pydanga_min = pydanga_sale = 0

        # 동,층정보 가져오기
        building, floor, dangi_name = extract_building_floor(address1)

        #print(f"address1: {address1}, Building: {building}, Floor: {floor}, Dangi Name: {dangi_name}")

        # 법정코드(시군구) 및 읍면동 가져오기
        sido_code, sido_name, sigungu_code, sigungu_name, eub_myeon_dong = extract_region_code(address1)
        # None 값을 빈 문자열로 변환하여 출력
        # print(f"{idx:<5}"
        #       f"{address1:<30}"
        #       f"{sido_code if sido_code else '':<10}"
        #       f"{sido_name if sido_name else '':<10}"
        #       f"{sigungu_code if sigungu_code else '':<10}"
        #       f"{sigungu_name if sigungu_name else '':<10}"
        #       f"{eub_myeon_dong if eub_myeon_dong else '없음':<10}")

        # 위도, 경도 가져오기 (0이면 None로 키에러외 기타등등)
        latitude, longitude = get_lat_lng(address1)
        print(f"주소: {address1}, 위도: {latitude}, 경도: {longitude}")

        # 데이터 저장
        # data_entry = {
        #     "사건번호": case_number,
        #     "구분": category,
        #     "주소1": address1,
        #     "주소2": address2,
        #     "지역": region,
        #     "법정동코드": sigungu_code,
        #     "시군구명": sigungu_name,
        #     "법정동명": eub_myeon_dong,
        #     "동": building,
        #     "층": floor,
        #     "건물m2": building_m2,
        #     "건물평수": building_py,
        #     "대지m2": land_m2,
        #     "대지평수": land_py,
        #     "감정금액": appraisal_price,
        #     "최저금액": min_price,
        #     "매각금액": sale_price,
        #     "최저퍼센트": f"{min_percent}%",
        #     "매각퍼센트": f"{sale_percent}%",
        #     "감정금액평단가": f"{pydanga_appraisal}", # 만단위
        #     "최저금액평단가": f"{pydanga_min}",
        #     "매각금액평단가": f"{pydanga_sale}",
        #     "매각일자": sales_date,
        #     "단지명": dangi_name,
        #     "기타": extra_info
        # }

        data_entry = {
            "case_number": case_number,
            "category": category,
            "address1": address1,
            "address2": address2,
            "region": region,
            "sigungu_code": sigungu_code,
            "sigungu_name": sigungu_name,
            "eub_myeon_dong": eub_myeon_dong,
            "building": building,
            "floor": floor,
            "building_m2": building_m2,
            "building_py": building_py,
            "land_m2": land_m2,
            "land_py": land_py,
            "appraisal_price": appraisal_price,
            "min_price": min_price,
            "sale_price": sale_price,
            "min_percent": f"{min_percent}%",
            "sale_percent": f"{sale_percent}%",
            "pydanga_appraisal": f"{pydanga_appraisal}",  # 만단위
            "pydanga_min": f"{pydanga_min}",
            "pydanga_sale": f"{pydanga_sale}",
            "sales_date": sales_date,
            "dangi_name": dangi_name,
            "extra_info": extra_info,
            "latitude": latitude,
            "longitude": longitude
        }
        #print(data_entry)
        #
        data_list.append(data_entry)

        # print(f"idx: {idx}")
        # print("=" * 80)
        # for key, value in data_entry.items():
        #     print(f"{key}: {value}")
        # print("=" * 80)

    except Exception as e:
        print("데이터 처리 오류:", e)

# 시군구등 법정코드 json 데이타 로딩
def load_json_data():
    json_filepath = "region_codes.json"  # JSON 파일 경로
    with open(json_filepath, 'r', encoding='utf-8') as file:
        return json.load(file)

# 시도,시군구,읍면동 파싱처리
def extract_region_code(address):
    """
    주소에서 시도 코드, 시도 이름, 시군구 코드, 시군구 이름, 그리고 읍/면/동을 추출합니다.
    시군구는 보다 구체적인(길이가 긴) 이름부터 매칭하여 처리합니다.
    :param address: 분석할 주소 (예: "경기 고양시 일산서구 덕이동 731-5, 에이동 1층101호 (덕이동,일산파크뷰) 외 3필지")
    :param json_data: 지역 정보를 담은 리스트 (JSON 데이터)
    :return: (sido_code, sido_name, sigungu_code, sigungu_name, eub_myeon_dong) 튜플
             해당 정보가 없으면 (None, None, None, None, None)을 반환.
    """
    for region in json_data:
        # "시도 이름"은 예: "경기,경기도"처럼 콤마로 구분되므로 리스트로 변환하고, 더 긴 이름을 사용 (예: "경기도")
        sido_names = [name.strip() for name in region["시도 이름"].split(",")]
        if any(sido in address for sido in sido_names):
            sido_code = region["시도 코드"]
            sido_name = max(sido_names, key=len)
            # 시군구 리스트를 이름 길이 내림차순으로 정렬하여 더 구체적인 이름을 먼저 매칭
            cities = sorted(region["시군구"], key=lambda x: len(x["시군구 이름"]), reverse=True)
            for city in cities:
                city_name = city["시군구 이름"]
                # 주소에 city_name이 포함되어 있는지 검사 (단순 포함 검사)
                if city_name in address:
                    sigungu_code = city["시군구 코드"]
                    sigungu_name = city_name
                    # 시군구 이름이 나타난 위치 이후의 문자열에서 읍/면/동 추출
                    city_index = address.find(city_name)
                    if city_index != -1:
                        sub_address = address[city_index + len(city_name):]
                        # 시군구 뒤에 바로 나오는 읍/면/동 단어 추출 (예: "덕이동")
                        match = re.search(r'\b([가-힣]+(?:읍|면|동))\b', sub_address)
                        eub_myeon_dong = match.group(1) if match else None
                    else:
                        eub_myeon_dong = None

                    return sido_code, sido_name, sigungu_code, sigungu_name, eub_myeon_dong

    return None, None, None, None, None


def main():
    global json_data, saved_count, data_list  # 전역 변수 사용

    # 크롬드라이버 화면없이 동작하게 처리하는 방법(배치개념에 적용)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    # 브라우져에서 웹드라이버인지 체크여부(navigator.webdriver 속성 제거)
    #chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    # 필요에 따라 추가 옵션 설정: --no-sandbox, --disable-dev-shm-usage 등

    #driver = webdriver.Chrome(options=chrome_options)
    driver = webdriver.Chrome()
    try:
        # 시군구등 법정코드 json 데이타 로딩
        json_data = load_json_data()

        driver.get("https://www.tankauction.com/")
        driver.implicitly_wait(1)
        #=====
        login(driver)
        time.sleep(2)

        # ======================================================================
        # 공지및 기타 팝업메뉴 제거
        close_popups(driver)

        # ======================================================================
        # "경매검색" 메뉴 클릭 (<a href="/ca/caList.php" ... >경매검색</a> 요소 선택)
        menu_search(driver)

        # 페이지 전환 및 로딩 대기 (필요 시 조정)
        time.sleep(2)

        # ======================================================================
        # 카테고리 선택 창 열기
        select_categories(driver)
        time.sleep(5)

        # 총 건수 가져오기
        total_records = get_total_count(driver)

        # 페이징 이동 및 데이터 처리
        navigate_pages(driver, total_records)

        # 마지막 남은 레코드 저장
        if data_list:
            print(f"마지막 저장 전 현재까지 저장 건수: {saved_count + len(data_list)} 건, 남은 배치: {len(data_list)} 건")
            auction_save_to_sqlite(data_list)
            saved_count += len(data_list)
            data_list.clear()
        print(f"총 저장 건수: {saved_count} 건")
        # 스크립트 종료 전에 현재 sale_edate(현재 날짜)를 파일에 저장
        save_last_sale_date(sale_edate)

    except Exception as e:
        print("오류 발생:", e)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()