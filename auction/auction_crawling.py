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
from auction_db_utils import auction_save_to_sqlite, auction_get_last_crawling_final_date
from common.vworld_utils import VWorldGeocoding
from config import AUCTION_DB_PATH, MAP_API_KEY, VWORLD_URL
from pubdata.public_land_lawd_code_db_utils import get_lawd_by_name

from auction_geocode_utils import (
    is_valid_latlng,
    retry_geocode_failed_address
)

# ------------------------------
# 스크립트 시작 시 현재 날짜 기준으로 srch_sale_edate를 설정하고,
# 검색시 srch_sale_sdate 는 DB에 저장된 마지막 crawling_last_date 를 기준으로 가져옵니다.
# 2025-01-01 ~ 2025-06-31 : 20,064건 => 처리
# 2025-07-01 ~ 2025-12-31 : 23,340건 => 처리
# 2026-01-01 ~ 2026-05-31 : 20,299건 => 처리
# 2026-06-01 ~ 2026-12-31 : 18,733건 => 처리
#
today = datetime.today().strftime("%Y-%m-%d")
#srch_sale_sdate = auction_get_last_crawling_final_date()
#srch_sale_edate = today
srch_sale_sdate = '2026-06-01'
srch_sale_edate = '2026-12-31'
# ------------------------------

# 저장 방식 선택: "csv" 또는 "sqlite"
SAVE_MODE = "sqlite"  # 원하는 방식으로 변경 가능 (예: "csv")
BATCH_SIZE = 300     # 레코드 1000건마다 저장

# 글로벌 변수 설정
page_list = "100"
data_list = []
saved_count = 0    # 누적 저장 건수

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
    # 1. 상단 '로그인' 버튼 클릭 (data-action="loginDivBtn" 속성을 가진 요소)
    login_button = WebDriverWait(driver, 3).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//*[@data-action='loginDivBtn']")
        )
    )
    login_button.click()

    # 2. 로그인 팝업이 표시될 때까지 대기
    login_popup = WebDriverWait(driver, 3).until(
        EC.visibility_of_element_located((By.ID, "FLOATING_CONTENT"))
    )

    # 디버깅을 위한 로그인 팝업 HTML 출력
    login_html = login_popup.get_attribute("outerHTML")
    print("로그인 팝업의 HTML 성공..")

    # 3. 아이디 및 비밀번호 입력
    username_field = login_popup.find_element(By.NAME, "client_id")
    password_field = login_popup.find_element(By.NAME, "passwd")
    username_field.send_keys("wfight69")
    password_field.send_keys("ahdtpddlta_0")

    # 4. 로그인 제출 버튼 클릭 (id="loginBtn")
    submit_button = WebDriverWait(login_popup, 3).until(
        EC.element_to_be_clickable((By.ID, "loginBtn"))
    )
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
    print("카테고리 선택 창 열기 시작.")
    # ======================================================================
    # 1. "복수선택" 버튼(id="btn_power")을 클릭하여 카테고리 선택 창 열기 (안전성 강화)
    try:
        category_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "btn_power"))
        )
        # 일반 클릭이 안 될 경우를 대비해 자바스크립트 강제 클릭 병행
        try:
            category_button.click()
        except Exception:
            driver.execute_script("arguments[0].click();", category_button)

        print("카테고리 선택 창 열기 완료.")
    except Exception as e:
        print("카테고리 선택 창 열기 중 오류 발생:", e)
        return  # 창을 못 열면 이후 진행이 의미 없으므로 중단

    # 잠시 대기 (모달/드롭다운이 로드될 시간 확보)
    time.sleep(2)

    # ======================================================================
    # 2. 매각전부 옵션 선택 (DOM 속성을 직접 제어하여 disabled 해제 및 value 부여)
    try:
        stat_select = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "stat"))
        )
        # JavaScript를 사용하여 '매각전부' 옵션 수정 (비활성화 해제 및 value 설정)
        driver.execute_script("""
            let option = [...document.querySelectorAll("#stat option")].find(opt => opt.textContent.includes("매각전부"));
            if (option) {
                option.removeAttribute("disabled");
                option.classList.remove("bg_gray");
                option.setAttribute("value", "12");
            }
        """)
        # Select 객체를 사용하여 수정된 옵션 선택
        select_obj = Select(stat_select)
        select_obj.select_by_value("12")         # 진행물건(11), 매각전부(12)

        print("매각전부 옵션 선택됨.")
        time.sleep(2)
    except Exception as e:
        print("매각전부 옵션 선택 중 오류 발생:", e)

    # ======================================================================
    # 3. 매각일자 설정
    try:
        bgnDt = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "bgnDt"))
        )
        endDt = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "endDt"))
        )
        bgnDt.clear()
        bgnDt.send_keys(srch_sale_sdate)
        endDt.clear()
        endDt.send_keys(srch_sale_edate)
        print(f"매각일자 설정 완료: 시작일자 {srch_sale_sdate}, 종료일자 {srch_sale_edate}")
        time.sleep(1)
    except Exception as e:
        print("매각일자 설정 중 오류 발생:", e)

    # ======================================================================
    # 4-1. 주거용 카테고리 체크박스 선택
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
        print("주거용 카테고리 선택 오류:", e)

    # 4-2. 상업 및 산업용 등 기타 카테고리 체크박스 선택
    for category in ["근린생활시설", "근린상가", "오피스텔(상업)", "숙박시설", "업무시설", "공장", "창고시설"]:
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
    # 5. 첫 번째 검색 실행 (총 건수 확인을 위함)
    try:
        search_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "btnSrch"))
        )
        try:
            search_button.click()
        except Exception:
            driver.execute_script("arguments[0].click();", search_button)
        print("btnSrch 검색 실행 완료.")

        # 결과가 로드될 때까지 대기 (#lsTbody 요소가 로드되길 기다림)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#lsTbody"))
        )
        time.sleep(3)
    except Exception as e:
        print("검색 실행 중 오류 발생:", e)
        return

    # ======================================================================
    # 6. 검색 목록수를 설정값(page_list)으로 변경
    try:
        data_size_select = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "dataSize"))
        )
        select_obj = Select(data_size_select)
        select_obj.select_by_value(page_list)
        print(f"목록수가 {page_list}으로 설정되었습니다.")
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

            # 1페이지는 기본적으로 로드되어 있으므로 2페이지부터 클릭 혹은 이동 처리
            if page_no > 1:
                try:
                    # data-page 속성을 가진 페이지 버튼 찾기 (예: id="loadPage_2", data-page="2")
                    page_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, f"div[data-page='{page_no}']"))
                    )

                    # 일반 클릭 시도 후 실패 시 자바스크립트 클릭 수행
                    try:
                        page_button.click()
                    except Exception:
                        driver.execute_script("arguments[0].click();", page_button)

                except Exception as e:
                    print(f"❌ {page_no} 페이지 버튼을 찾는 중 오류 발생 (마지막 페이지 도달 가능성):", e)
                    break

            time.sleep(5)  # 페이지 로딩 대기

            # 레코드 파싱 및 데이터 저장
            record_parsing_list(driver, page_no)

        except Exception as e:
            print("❌ 페이지 이동 중 오류 발생 또는 마지막 페이지 도달:", e)
            break


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

        # ============================================================
        # 면적 정보 추출
        #
        # 기존 1번 방식 + 2번 방식 보완
        #
        # 처리 가능한 예:
        #
        # 건물 84.8895㎡(25.679평), 대지권 46.6082㎡(14.099평)
        # 건물 161.79㎡(48.941평), 토지 434.754㎡(131.513평)
        #
        # 건물 84.8895㎡ (25.679평)
        # 대지권 46.6082㎡ (14.099평)
        #
        # 건물 991㎡(299.778평)
        # 토지 5371㎡(1624.728평)
        #
        # 건물 44.27㎡(13.392평), 토지 매각제외
        # ============================================================

        building_m2 = ''
        building_py = ''
        land_m2 = ''
        land_py = ''
        area_py = 0

        # ------------------------------------------------------------
        # 1. 우선 기존 1번 방식으로
        #    "건물 + 대지권"이 한 세트로 존재하는 경우 추출
        #
        # 기존:
        # 건물 84.8895㎡(25.679평),
        # 대지권 46.6082㎡(14.099평)
        # ------------------------------------------------------------
        area_match = re.search(
            r'건물\s*'
            r'([\d,.]+)\s*㎡\s*'
            r'\(\s*([\d,.]+)\s*평\s*\)'
            r'\s*,?\s*'
            r'대지권\s*'
            r'([\d,.]+)\s*㎡\s*'
            r'\(\s*([\d,.]+)\s*평\s*\)',
            row_text
        )

        if area_match:
            building_m2 = area_match.group(1).replace(',', '')
            building_py = area_match.group(2).replace(',', '')

            land_m2 = area_match.group(3).replace(',', '')
            land_py = area_match.group(4).replace(',', '')

        # ------------------------------------------------------------
        # 2. 위의 기존 방식으로 추출되지 않은 경우
        #    건물 면적을 독립적으로 다시 검색
        #
        # 이렇게 하면 대지권이 없는 데이터도 처리 가능
        #
        # 예:
        # 건물 991㎡(299.778평), 토지 5371㎡(1624.728평)
        #
        # 건물 44.27㎡(13.392평), 토지 매각제외
        # ------------------------------------------------------------
        if not building_m2:

            building_match = re.search(
                r'건물\s*'
                r'([\d,.]+)\s*㎡\s*'
                r'\(\s*([\d,.]+)\s*평\s*\)',
                row_text
            )

            if building_match:
                building_m2 = (
                    building_match
                    .group(1)
                    .replace(',', '')
                )

                building_py = (
                    building_match
                    .group(2)
                    .replace(',', '')
                )

        # ------------------------------------------------------------
        # 3. 대지권이 추출되지 않은 경우
        #    "대지권"을 독립적으로 다시 검색
        # ------------------------------------------------------------
        if not land_m2:

            land_match = re.search(
                r'대지권\s*'
                r'([\d,.]+)\s*㎡\s*'
                r'\(\s*([\d,.]+)\s*평\s*\)',
                row_text
            )

            if land_match:
                land_m2 = (
                    land_match
                    .group(1)
                    .replace(',', '')
                )

                land_py = (
                    land_match
                    .group(2)
                    .replace(',', '')
                )

        # ------------------------------------------------------------
        # 4. "대지권"이 없는 경우
        #    일반 "토지" 면적 검색
        #
        # 예:
        # 건물 161.79㎡(48.941평),
        # 토지 434.754㎡(131.513평)
        #
        # 중요:
        # "토지·건물 일괄매각"
        # "토지 매각제외"
        # 같은 문장은 숫자+㎡가 없으므로 매칭되지 않음
        # ------------------------------------------------------------
        if not land_m2:

            land_match = re.search(
                r'토지\s*'
                r'([\d,.]+)\s*㎡\s*'
                r'\(\s*([\d,.]+)\s*평\s*\)',
                row_text
            )

            if land_match:
                land_m2 = (
                    land_match
                    .group(1)
                    .replace(',', '')
                )

                land_py = (
                    land_match
                    .group(2)
                    .replace(',', '')
                )

        # ------------------------------------------------------------
        # 5. 평단가 계산용 건물평수
        # ------------------------------------------------------------
        if building_py:

            try:
                area_py = float(
                    building_py
                )

            except (ValueError, TypeError):
                area_py = 0

        else:

            area_py = 0

        # ============================================================
        # 금액 정보 추출
        # HTML 구조 변경으로 인해 줄 위치를 기준으로 찾지 않고
        # 금액 형태(233,000,000 등)를 직접 추출
        # ============================================================
        appraisal_price = 0
        min_price = 0
        sale_price = 0
        try:
            # 최소 6자리 이상의 콤마 포함 금액만 추출
            # 예:
            # 233,000,000
            # 114,170,000
            # 119,500,099
            price_matches = re.findall(
                r'(?<![\d.])(\d{1,3}(?:,\d{3}){2,})(?![\d.])',
                row_text
            )

            prices = []

            for price in price_matches:
                try:
                    value = int(price.replace(',', ''))

                    # 중복 제거
                    if value not in prices:
                        prices.append(value)

                except:
                    pass

            if len(prices) >= 1:
                appraisal_price = prices[0]

            if len(prices) >= 2:
                min_price = prices[1]

            if len(prices) >= 3:
                sale_price = prices[2]

        except Exception as e:
            print(f"금액 파싱 오류 idx={idx}: {e}")


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
        #sido_code, sido_name, sigungu_code, sigungu_name, eub_myeon_dong = extract_region_code(address1)

        # ------------------------------------------------------------
        # 11. 법정동 코드
        region = ""
        sigungu_code = ""
        sigungu_name = ""
        umd_name = ""

        # 필요시 다시 활성화
        try:
            region_info = extract_region_code(address1)
            region = region_info.get("region", "")
            lawd_cd = region_info.get("lawd_cd", "")
            sigungu_code = region_info.get("sigungu_code", "")
            sigungu_name = region_info.get("sigungu_name", "")
            umd_name = region_info.get("umd_name", "")
        except Exception as e:
            print(f"법정동 코드 파싱 오류 idx={idx}: {e}")

        # ------------------------------------------------------------
        # 12. 위도 / 경도
        latitude = "0"
        longitude = "0"

        # [기존 성공 로직 유지]
        # 기존과 동일하게 address1 전체를 parcel로 먼저 조회한다.
        # 이 조회가 성공하면 추가 보완 로직은 실행하지 않는다.
        #-----------------------------------------------
        try:
            geo_service = VWorldGeocoding(MAP_API_KEY)

            # ★ 기존 코드 그대로
            latitude, longitude = geo_service.get_lat_lng(
                address1,
                "parcel"
            )

            # --------------------------------------------------------
            # ★ 추가된 부분
            #
            # 기존 방식이 성공했으면 아무것도 하지 않음.
            #
            # CSV 실패건처럼
            # latitude/longitude가 0인 경우에만
            # 추가 주소 후보로 재조회
            # --------------------------------------------------------
            if not is_valid_latlng(
                    latitude,
                    longitude
            ):
                latitude, longitude = (
                    retry_geocode_failed_address(
                        geo_service=geo_service,
                        case_number=case_number,
                        address1=address1,
                        address2=address2
                    )
                )

        except Exception as e:
            # ========================================================
            # ★ 중요
            #
            # VWorld API 오류
            # 네트워크 오류
            # 주소변환 오류
            # retry 함수 오류
            #
            # 어떤 예외가 발생해도
            # 해당 경매 레코드를 버리지 않는다.
            # ========================================================
            latitude = "0"
            longitude = "0"

            print(
                f"좌표 변환 오류 idx={idx}: {e}"
            )

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
            "eub_myeon_dong": umd_name,
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
        print(data_entry)
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

    # 2. 주소로 법정동 코드 조회 로직 (실제 DB나 API 연동 필요)
    # ---------------------------------------------------------
    # 리턴 데이터 조립 및 필드 설명
    # ---------------------------------------------------------
    # 1. lawd_cd: 전체 법정동 코드 (예: 4157010300)
    # 2. lawd_name: 전체 주소 명칭 (예: 경기도 수원시 권선구 호매실동)
    # 3. region: 광역 지자체 이름 (예: 경기도, 경상북도)
    # 4. sigungu_code: 법정동 코드 앞 5자리 (예: 41570)
    # 5. sigungu_name: 기초 지자체 이름 (예: 수원시 권선구, 하동군)
    # 6. umd_name: 가장 하위 행정구역 명칭 (예: 호매실동, 진교면)
    # ---------------------------------------------------------
    row = get_lawd_by_name(address) or {}

    lawd_cd = row.get("lawd_cd", "")
    lawd_name = row.get("lawd_name", "")
    region = row.get("region", "")
    sigungu_code = row.get("sigungu_code", "")
    sigungu_name = row.get("sigungu_name", "")
    umd_name = row.get("umd_name", "")

    return {
        "lawd_cd": lawd_cd,
        "lawd_name": lawd_name,
        "region": region,
        "sigungu_code": sigungu_code,
        "sigungu_name": sigungu_name,
        "umd_name": umd_name
    }

# 크롬드라이버 화면없이 동작하게 처리하는 방법(배치개념에 적용)
def create_driver():
    chrome_options = Options()

    # 최신 Chrome 헤드리스 모드
    chrome_options.add_argument("--headless=new")

    # 헤드리스 기본 화면이 작으면 반응형 UI나 배너가 요소를 가릴 수 있음
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--force-device-scale-factor=1")

    # 자동화 안정성
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-search-engine-choice-screen")

    # 백그라운드 실행 시 타이머/렌더링 제한 완화
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-renderer-backgrounding")

    # 네트워크 및 렌더링 안정화
    chrome_options.add_argument("--disable-features=TranslateUI")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--no-default-browser-check")

    # 자동화 탐지 표시 일부 제거
    chrome_options.add_experimental_option(
        "excludeSwitches",
        ["enable-automation", "enable-logging"]
    )
    chrome_options.add_experimental_option(
        "useAutomationExtension",
        False
    )

    # 페이지가 완전히 로딩될 때까지 기다림
    chrome_options.page_load_strategy = "normal"

    driver = webdriver.Chrome(options=chrome_options)

    # 옵션과 별개로 실제 WebDriver 창 크기도 지정
    driver.set_window_size(1920, 1080)

    driver.set_page_load_timeout(60)
    driver.set_script_timeout(60)

    return driver

def main():
    global json_data, saved_count, data_list  # 전역 변수 사용

    # 크롬드라이버 화면없이 동작하게 처리하는 방법(배치개념에 적용)
    driver = create_driver()

    try:
        # 시군구등 법정코드 json 데이타 로딩
        #json_data = load_json_data()

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

    except Exception as e:
        print("오류 발생:", e)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()