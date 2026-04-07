from selenium import webdriver
from selenium.common import StaleElementReferenceException, TimeoutException, WebDriverException
from selenium.common.exceptions import UnexpectedAlertPresentException, NoAlertPresentException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import time
import re
import json
import os
import requests

from webdriver_manager.chrome import ChromeDriverManager

from jumpo.jumpo_crawling import detail_driver
#
from npl_db_utils import npl_save_to_sqlite, npl_drop_table
from config import NPL_DB_PATH, MAP_API_KEY, VWORLD_URL

# 저장파일명
last_file_name = os.path.join(NPL_DB_PATH, "last_npl_date.txt")

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
#BATCH_SIZE = 100     # 레코드 1000건마다 저장
BATCH_SIZE = 10     # 레코드 1000건마다 저장

# 글로벌 변수 설정
page_list = "100"
data_list = []
saved_count = 0    # 누적 저장 건수
map_api_key = "AIzaSyBzacpsf9Cw3CRRqWXUHbHkRDNbYlaXGCI"    # 구글맴 api_key
# —————————————————————————————————————————————————————————
# 1) 전역 detail_driver 선언
detail_driver = None
# —————————————————————————————————————————————————————————

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
def login_old(driver):
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

# 로그인처리 (개선버전)
def login(driver):
    try:
        # 로그인 버튼 대기
        login_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//*[@onclick='floating_div(400);']"))
        )

        # 화면 안으로 스크롤
        driver.execute_script("arguments[0].scrollIntoView(true);", login_button)
        time.sleep(0.5)

        # 먼저 일반 클릭 시도
        try:
            login_button.click()
        except WebDriverException:
            # element click intercepted 등 나오면 JS로 강제 클릭
            driver.execute_script("arguments[0].click();", login_button)

        # 로그인 팝업이 표시될 때까지 대기
        login_popup = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.ID, "FLOATING_CONTENT"))
        )

        username_field = login_popup.find_element(By.NAME, "client_id")
        password_field = login_popup.find_element(By.NAME, "passwd")
        username_field.clear()
        password_field.clear()
        username_field.send_keys("wfight69")
        password_field.send_keys("ahdtpddlta_0")

        submit_button = login_popup.find_element(
            By.XPATH, ".//a[contains(@onclick, 'login();')]"
        )
        submit_button.click()

        print("로그인 시도 완료.")
        # 필요하면 로그인 성공 여부 체크 로직을 추가해도 됨 (예: 로그아웃 버튼 존재 여부)
    except Exception as e:
        print("로그인 오류:", e)


# 메뉴처리
def menu_search(driver):
    try:
        # ======================================================================
        # "경매검색" 메뉴 클릭 (<a href="/ca/caList.php" ... >경매검색</a> 요소 선택)
        npl_search = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@href='/ca/caList.php' and contains(text(), '경매검색')]"))
        )
        npl_search.click()
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
    # [추가] 시/도 옵션 선택(특정지역 테스트용)
    # try:
    #     stat_select = WebDriverWait(driver, 10).until(
    #         EC.presence_of_element_located((By.ID, "siCd"))
    #     )
    #     select_obj = Select(stat_select)
    #     select_obj.select_by_value("28")    # 인천(28)
    #     print("인천광역시(28) 옵션 선택됨.")
    #     time.sleep(2)
    # except Exception as e:
    #     print("시/도 옵션 선택 중 오류 발생:", e)

    # [추가] 매각전부 옵션 선택
    try:
        stat_select = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "stat"))
        )
        select_obj = Select(stat_select)
        select_obj.select_by_value("11")    # 진행물건(11), 매각전부(12)
        print("진행물건(11) 옵션 선택됨.")
        time.sleep(2)
    except Exception as e:
        print("매각전부 옵션 선택 중 오류 발생:", e)

    # [추가] 매각일자 설정
    # try:
    #     bgnDt = WebDriverWait(driver, 5).until(
    #         EC.presence_of_element_located((By.ID, "bgnDt"))
    #     )
    #     endDt = WebDriverWait(driver, 5).until(
    #         EC.presence_of_element_located((By.ID, "endDt"))
    #     )
    #     bgnDt.clear()
    #     bgnDt.send_keys(sale_sdate)
    #     endDt.clear()
    #     endDt.send_keys(sale_edate)
    #     print(f"매각일자 설정 완료: 시작일자 {sale_sdate}, 종료일자 {sale_edate}")
    #     time.sleep(1)
    # except Exception as e:
    #     print("매각일자 설정 중 오류 발생:", e)
    #
    # ======================================================================
    # 주거용 카테고리 선택
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

    #-----------------------------------------------------------------------
    # 상업및 산업용 체크박스 선택처리(관심 ** 테스트용)
    # try:
    #     categories = ["숙박시설"]
    #     for category in categories:
    #         checkbox = WebDriverWait(driver, 5).until(
    #             EC.element_to_be_clickable((By.XPATH,
    #                                         f"//*[@id='ulGrpCtgr_20']//span[contains(text(), '{category}')]/preceding-sibling::input[@type='checkbox']"))
    #         )
    #         if not checkbox.is_selected():
    #             checkbox.click()
    #             print(f"'{category}' 체크박스 선택됨.")
    # except Exception as e:
    #     print("카테고리 선택 오류:", e)

    # 상업및 산업용 체크박스 선택처리(관심 ** 테스트용)
    try:
        # '상업용' 체크박스를 트리거할 label 클릭
        label = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, "//label[@for='chkGrpCtgr_20']"))
        )
        label.click()
        print("✅ '상업용' 카테고리 클릭 완료 (chkCtgrMulti(20,1) 호출됨)")
    except Exception as e:
        print("❌ 카테고리 클릭 실패:", e)

    # 토지
    # try:
    #     # '토지' 체크박스를 트리거할 label 클릭
    #     label = WebDriverWait(driver, 30).until(
    #         EC.element_to_be_clickable((By.XPATH, "//label[@for='chkGrpCtgr_30']"))
    #     )
    #     label.click()
    #     print("✅ '토지' 카테고리 클릭 완료 (chkCtgrMulti(30,1) 호출됨)")
    # except Exception as e:
    #     print("❌ 카테고리 클릭 실패:", e)

    # ======================================================================
    # 첫번째 검색으로 페이지에 총건수를 가져오기 위함.
    driver.execute_script("srchClick();")
    print("srchClick() 검색함수 실행 완료.")

    # 결과가 로드될 때까지 대기 (#lsTbody 요소가 로드되길 기다림)
    tbody = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#lsTbody"))
    )
    # 형식적경매 결과는 출력하지 않고 잠시 대기만 함
    time.sleep(2)

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
    tbody = WebDriverWait(driver, 8).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#lsTbody"))
    )
    # tbody 안의 모든 tr 요소 선택
    rows = tbody.find_elements(By.TAG_NAME, "tr")
    for idx, row in enumerate(rows, start=1):
        row_text = row.text.strip()

        #----------------------------
        # npl파악위한 근저당 채권최고액(말소기준권리), 임의(강제)경매 청구금액, 임의(강제)경매 청구자
        # tr 안의 hidden input 중 name 또는 id가 Tid_로 시작하는 것을 찾기
        tid_input = row.find_element(By.XPATH, './/input[starts-with(@id, "Tid_")]')
        tid = tid_input.get_attribute("value")

        # print(f"{idx}: tid = {tid}")
        npl_info = npl_extract_info(driver, row_text, tid)
        if npl_info is None:
            continue  # NPL 아님, 다음 로우로

        # info 언패킹
        #deposit_value, min_price, bond_max_amount, bond_claim_amount, start_decision_date, auction_method, auction_applicant, notice_text = npl_info

        # 상세정보 처리
        extract_info(row_text, idx, npl_info)

        # 1000건마다 저장 처리
        if len(data_list) >= BATCH_SIZE:
            print(f"저장 전 현재까지 저장 건수: {saved_count + len(data_list)} 건, 이번 배치: {len(data_list)} 건")
            npl_save_to_sqlite(data_list)
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
            safe_execute_script(driver, f"srchList({page_no}); chkEachlist();")
            time.sleep(5)  # 페이지 로딩 대기

            # 레코드 파싱 및 데이터 저장
            record_parsing_list(driver, page_no)

        except WebDriverException as e:
            print("WebDriver error, retrying page:", e)
            # (위 safe_execute_script가 이미 재시작까지 처리해 줍니다)
            continue
        # except Exception as e:
        #     print("❌ 페이지 이동 중 오류 발생 또는 마지막 페이지 도달:", e)
        #     break

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
        "type": "road",  # road: 도로명, parcel: 지번
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


# tid번호를 이용한 npl여부츨 체크함
def npl_extract_info(driver, row_text, tid):
    try:
        lines = row_text.split('\n')

        #print('== row_text: ' + row_text)

        # 금액 정보 추출
        idx_price_start = next(
            i for i, line in enumerate(lines) if ("토지" in line or "건물" in line) and "매각" in line and "매각제외" not in line) + 1
        appraisal_price = lines[idx_price_start]  # 감정금액
        min_price = lines[idx_price_start + 1]  # 최저금액
        bid_count = lines[idx_price_start + 2].replace(',', '')  # 유찰회수
        bid_text = lines[idx_price_start + 3].replace(',', '')  # 낙찰가율
        bid_rate = bid_text.replace("(", "").replace(")", "")
        sale_decision_date_text = lines[idx_price_start + 5].replace(',', '')  # 매각기일
        sale_decision_date = convert_to_iso(sale_decision_date_text)  # 매각기일
        print('-')
        print('== TID: ' + tid )
        print('== 감정평가금액: ' + appraisal_price)
        print('== 최저낙찰가:  ' + min_price)
        print('== 최저유찰회수: ' + bid_count)
        print('== 낙찰비율: ' + bid_rate)
        print('== 매각일자: ' + sale_decision_date)

        bond_max_amount = '0'         # 채권채고액
        bond_claim_amount = '0'       # 채권청구액
        auction_method = ''         # 경매방식(임의, 강제)
        auction_applicant = '신협'   # 경매신청자

        # 현재 드라이버: driver (기존 창)
        main_window = driver.current_window_handle

        # 2) 새 탭 열기 & 전환
        #tid = "2231582"
        url = f"https://www.tankauction.com/ca/caView.php?tid={tid}"
        driver.execute_script(f"window.open('{url}', '_blank');")
        # 새 탭으로 스위치
        driver.switch_to.window(driver.window_handles[-1])
        wait = WebDriverWait(driver, 1)

        # '유치권/선순위 가처분/대항력 있는 임차인' 텍스트가 있는 span 요소 대기 및 추출
        notice_text = ''
        opposability_status = ''    # 임차권등기 및 대항력여부
        try:

            red_notice_span = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//span[contains(@class,'red') and contains(@class,'spanBox')]")
                )
            )
            # 모든 공백(스페이스, 탭, 줄바꿈 등)을 제거하려면:
            raw = red_notice_span.text
            notice_text = re.sub(r"\s+", "", raw)

            # 임차권등기' 또는 '대항력있는임차인'이 포함여부
            opposability_status = determine_opposability_status(notice_text)
        except Exception as e:
            print("오류 발생:", e)

        # '개시결정' 레이블 옆의 날짜를 가져오는 예시
        start_decision_date = ''
        try:
            start_decision_td = wait.until(EC.presence_of_element_located((By.XPATH, "//th[contains(text(), '개시결정')]/following-sibling::td[1]")))
            raw_text = start_decision_td.text.strip()  # 예: "2014-01-21(강제경매)"

            # "(" 이후 내용을 제거하여 날짜만 추출
            match = re.match(r"^([^\(]+)", raw_text)
            start_decision_date = match.group(1).strip() if match else raw_text
        except Exception as e:
            print("개시결정 날짜 추출 오류:", e)

        # 4. 보증금 요소 대기 및 추출(목록에서 맨처음께 나옴)
        deposit_text = ''
        try:
            deposit_td = wait.until(EC.presence_of_element_located((By.XPATH, "//td[contains(text(), '보:')]")))
            deposit_text = deposit_td.text.strip()
            match = re.search(r"보:([\d,]+)", deposit_text)
            deposit_value = match.group(1) if match else 0
        except (Exception, StaleElementReferenceException):
            deposit_value = 0

        # 채권합계금액 추출
        try:
            bond_span = wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(text(), '채권합계금액')]")))
            bond_text = bond_span.text.strip()
            # 채권금액 적용처리: # (채권합계금액:313,701,101원)
            bond_total_amount = extract_and_format(bond_text)

        except (StaleElementReferenceException, TimeoutException):
            bond_total_amount = 0

        print("📌 채권합계금액:", bond_total_amount)

        # 결과 저장용 리스트
        result_data = []
        headers = "순서", "권리종류", "권리자", "채권금액", "비고"
        try:
            # 채권채고액 및 임의,강제경매 구하기
            # 테이블의 모든 tr을 기다림
            rows = wait.until(EC.presence_of_all_elements_located(
                    (By.XPATH, "//div[@id='lyCnt_regist' and contains(@class,'clear')]"
                               "//table[@class='Ltbl_list']//tbody//tr")
                ))
            for row in rows:
                try:
                    tds = row.find_elements(By.TAG_NAME, "td")
                    if len(tds) < 6:
                        continue  # td 수가 적으면 건너뜀

                    # 비고 컬럼 텍스트
                    seq =  tds[0].text.strip() # 순서
                    right_type = tds[2].text.strip()  # 권리종류
                    bond_user = tds[3].text.strip()   # 권리자
                    bond_text = tds[4].text.strip()   # 채권금액
                    remarks = tds[5].text.strip()

                    # 채권금액 적용처리
                    bond_amt = extract_and_format(bond_text)

                    # 조건 1: 말소기준등기 포함 여부
                    if "말소기준등기" in remarks or "강제경매" in right_type or "임의경매" in right_type:
                        #
                        if "말소기준등기" in remarks:
                            bond_max_amount = bond_amt

                        if "강제경매" in right_type or "임의경매" in right_type:
                            auction_method = right_type     # 경매형식
                            auction_applicant = bond_user.replace("\n", "")   # 경매신청자
                            bond_claim_amount = bond_amt    # 채권청구액

                        # 행 데이터를 리스트로 저장
                        row_data = [
                            seq,  # 순서
                            right_type,  # 권리종류
                            bond_user,  # 권리자
                            bond_amt,  # 채권금액
                            remarks  # 비고
                        ]
                        result_data.append(row_data)

                except StaleElementReferenceException:
                    continue

            # 결과 출력
            print(headers)
            for row in result_data:
                print(row)

        except (StaleElementReferenceException, TimeoutException):
            print("📌 건물등기 조건찾기 어려움:")

        # 7) 새 탭 닫고 메인 탭으로 복귀
        driver.close()
        driver.switch_to.window(main_window)

        print('--')
        print("📌 보증금 추출 목록:", deposit_text)
        print("== 임차보증금금액:", deposit_value)
        print('== 감정평가금액: ' + appraisal_price)
        print('== 최저낙찰가: ' + min_price)         # 최저낙찰가
        print('== 유찰회수: ' + bid_count)
        print('== 낙찰비율: ' + bid_rate)
        print("== 채권합계금액:", bond_total_amount)
        print('== 채권최고액: ' + bond_max_amount)   # 채권최고액
        print('== 채권청구액: ' + bond_claim_amount)
        print('== 경매개시일자: ' + start_decision_date)   # 2024-03-01(임의경매)
        print('== 경매매각일자: ' + sale_decision_date)   # 2025-03-01(최종매각일자)
        print('== 경매청구방식: ' + auction_method)   # 임의경매, 강제경매
        print('== 경매신청자: ' + auction_applicant)
        print('== 비고내역: ' + notice_text)    # 임차권등기/유치권/법정지상권등
        print('== 임차권등기여부: ' + opposability_status)

        # NPL물건여부 평가
        is_npl = evaluate_npl(min_price, bond_max_amount, bond_claim_amount)
        result_label = "NPL물건" if is_npl else "일반물건"
        print('** 물건구분: ' + result_label)
        if not is_npl:
            return None

        # NPL일 때 필요한 값 반환
        return deposit_value, bond_total_amount, appraisal_price, min_price, bid_count, bid_rate, bond_max_amount, bond_claim_amount, start_decision_date, sale_decision_date, auction_method, auction_applicant, notice_text, opposability_status, tid

    except Exception as e:
            print("데이터 처리 오류:", e)
            return None

# 임차권등기 대향력여부
def determine_opposability_status(notice_text):
    """
    notice_text 문자열 안에 '임차권등기' 또는 '대항력있는임차인'이 포함되어 있으면
    opposability_status를 'Y'로, 그렇지 않으면 'N'으로 반환합니다.
    """
    keywords = ["임차권등기", "대항력있는임차인"]
    for kw in keywords:
        if kw in notice_text:
            return 'Y'
    return 'N'

# 날짜형식을 변환처리한다.
def convert_to_iso(date_str):
    """
    "YY.MM.DD" 형식의 문자열을 받아 "YYYY-MM-DD" 형식으로 반환합니다.
    예: "25.03.01" → "2025-03-01"
    """
    # "YY.MM.DD" 형식이 맞는지 간단히 확인
    parts = date_str.split('.')
    if len(parts) != 3:
        raise ValueError(f"잘못된 형식: {date_str}")

    yy, mm, dd = parts
    # 두 자리 연도를 네 자리로 변환 (2000년대 기준)
    yyyy = f"20{yy}"
    # 검증을 위해 datetime으로 파싱했다가 다시 포맷팅
    try:
        dt = datetime.strptime(f"{yyyy}-{mm}-{dd}", "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d")
    except ValueError as e:
        raise ValueError(f"날짜 변환 오류: {e}")


# 금액만 추출 후 정수로 변환하고, 천 단위 콤마 포맷 적용
def extract_and_format(text):
    m = re.search(r'(\d[\d,]*)', text)
    if not m:
        return "0"
    # 쉼표 제거 후 정수로 변환
    value = int(m.group(1).replace(',', ''))
    # 천 단위 콤마 추가
    return f"{value:,}"


# npl여부를 체크: 최저낙찰가, 채권채고액, 채권청구액
def evaluate_npl(lowest_price_str, max_claim_str, claim_amount_str):
    # Remove commas and convert to integers
    lowest_price = int(lowest_price_str.replace(',', '').strip())
    max_claim = int(max_claim_str.replace(',', '').strip())
    claim_amount = int(claim_amount_str.replace(',', '').strip())

    # If max_claim is zero, use claim_amount
    if max_claim == 0:
        max_claim = claim_amount

    # Compare values
    is_npl = max_claim > lowest_price

    return is_npl


# 주소로 시군구 데이타 파싱및 분석
def extract_info(row_text, idx, npl_info):
    try:
        # info 언패킹
        deposit_value, bond_total_amount, appraisal_price, min_price, bid_count, bid_rate, bond_max_amount, bond_claim_amount, start_decision_date, sale_decision_date, auction_method, auction_applicant, notice_text, opposability_status, tid = npl_info

        # 관심 ** 이런게 들어가면 2번째 라인으로 사건번호로 인식되어 제거처리
        lines = [line for line in row_text.split('\n') if not line.startswith('관심')]

        # 기본 정보 추출
        category = lines[0]  # 구분 (예: 아파트)
        case_number = lines[1]  # 사건번호
        address1 = lines[2]  # 주소1
        address2 = lines[3] if lines[3].startswith('(') else ''  # 주소2 (괄호 포함)

        # 주소 세부 정보 추출 (지역, 시군구, 법정동)
        address_parts = address1.split()

        # 지역코드 = 시도이름
        # region = address_parts[0] if len(address_parts) > 0 else ''
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

        # 판매금액및 비율 정보 추출
        sale_price = 0
        min_percent = bid_rate
        sale_percent = ''

        # 기타 정보 추출
        extra_info = ', '.join([line for line in lines if '계' in line or '토지' in line or '건물' in line or '임차인' in line])

        # 평단가 계산
        if area_py != 0:
            pydanga_appraisal = int(int(appraisal_price.replace(",", "")) / (area_py * 10000))
            pydanga_min = int(int(min_price.replace(",", "")) / (area_py * 10000))
            pydanga_sale = 0
        else:
            pydanga_appraisal = pydanga_min = pydanga_sale = 0

        # 동,층정보 가져오기
        building, floor, dangi_name = extract_building_floor(address1)

        #print(f"address1: {address1}, Building: {building}, Floor: {floor}, Dangi Name: {dangi_name}")

        # 법정코드(시군구) 및 읍면동 가져오기
        lawd_cd, sido_code, sido_name, sigungu_code, sigungu_name, eub_myeon_dong = extract_region_code(address1)
        # None 값을 빈 문자열로 변환하여 출력
        # print(f"{idx:<5}"
        #       f"{address1:<30}"
        #       f"{sido_code if sido_code else '':<10}"
        #       f"{sido_name if sido_name else '':<10}"
        #       f"{sigungu_code if sigungu_code else '':<10}"
        #       f"{sigungu_name if sigungu_name else '':<10}"
        #       f"{eub_myeon_dong if eub_myeon_dong else '없음':<10}")

        # 위도, 경도 가져오기 (0이면 None로 키에러외 기타등등) - 괄호제거
        lat_lng_address = address2.replace('(', '').replace(')', '')
        latitude, longitude = get_lat_lng(lat_lng_address)
        print(f"주소: {lat_lng_address}, 위도: {latitude}, 경도: {longitude}")

        # 임의경매신청자가 개인인경우(default N)
        # 한글 3자이며 '신협', '금고', '은행' 포함하지 않을 경우 'Y', 아니면 'N'
        if (
                re.fullmatch(r'[가-힣]{3}', auction_applicant) and
                not any(keyword in auction_applicant for keyword in ['신협', '금고', '은행'])
        ):
            personal_status = 'Y'
        else:
            personal_status = 'N'

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
            "lawd_cd": lawd_cd,
            "region": sido_name,
            "sigungu_code": sigungu_code,
            "sigungu_name": sigungu_name,
            "eub_myeon_dong": eub_myeon_dong,
            "building": building,
            "floor": floor,
            "building_m2": building_m2,
            "building_py": building_py,
            "land_m2": land_m2,
            "land_py": land_py,
            "appraisal_price": appraisal_price,         # 감정가
            "min_price": min_price,                     # 최저가
            "sale_price": sale_price,
            "min_percent": f"{min_percent}",
            "sale_percent": f"{sale_percent}",
            "pydanga_appraisal": f"{pydanga_appraisal}",  # 만단위
            "pydanga_min": f"{pydanga_min}",
            "pydanga_sale": f"{pydanga_sale}",
            "sales_date": sale_decision_date,           # 매각일자
            "dangi_name": dangi_name,
            "extra_info": extra_info,
            "bid_count": bid_count,                     # 유찰회수
            "bid_rate": bid_rate,                       # 유찰비율
            "deposit_value": deposit_value,             # 임차보증금금액
            "bond_total_amount": bond_total_amount,     # 총채권합계금액
            "bond_max_amount": bond_max_amount,         # 채권최고액
            "bond_claim_amount": bond_claim_amount,     # 채권청구액
            "start_decision_date": start_decision_date, # 경매개시일자
            "sale_decision_date": sale_decision_date,   # 경매매각일자
            "auction_method": auction_method,           # 경매청구방식(임의경매, 강제경매)
            "auction_applicant": auction_applicant,     # 경매신청자
            "notice_text": notice_text,                 # 비고내역(임차권등기/유치권/법정지상권등)
            "opposability_status": opposability_status, # 임차권등기/대항력있는임차인 여부(Y/N)
            "personal_status": personal_status,         # 임의경매신청자가 개인인경우(default N)
            "latitude": latitude,
            "longitude": longitude,
            "tid": tid
        }
        print("===== extract_info() ======= ")
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
# 차후 public_data에 lawd_code 테이블에서 (법정동코드내역: lawd_cd, lawd_name)
# public_land_lawd_code_db_utils.py에 get_lawd_by_name(lawd_name)을 호출하여 법정동코드(lawd_cd)를 가져오는 방식으로 변경할 수 있음
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
            #sido_name = max(sido_names, key=len)
            sido_name = sido_names[1]
            # 시군구 리스트를 이름 길이 내림차순으로 정렬하여 더 구체적인 이름을 먼저 매칭
            cities = sorted(region["시군구"], key=lambda x: len(x["시군구 이름"]), reverse=True)
            for city in cities:
                city_name = city["시군구 이름"]
                # 주소에 city_name이 포함되어 있는지 검사 (단순 포함 검사)
                if city_name in address:
                    sigungu_code = city["시군구 코드"]   # 법정동코드개념
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
                    lawd_cd = sigungu_code

                    return lawd_cd, sido_code, sido_name, sigungu_code, sigungu_name, eub_myeon_dong

    return None, None, None, None, None


# 1) 드라이버 초기화 함수
def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_experimental_option("detach", True)
    return webdriver.Chrome(
        # service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

# 2) 안전하게 URL 호출
def safe_get(driver, url):
    try:
        driver.get(url)
    except WebDriverException as e:
        if 'invalid session id' in str(e).lower():
            driver.quit()
            # driver = init_driver()
            # login(driver)
            # menu_search(driver)
            # select_categories(driver)
            # return safe_get(driver, url)
        else:
            raise
    return driver

# 3) 안전하게 execute_script
def safe_execute_script(driver, script):
    try:
        return driver.execute_script(script)
    except WebDriverException as e:
        if 'invalid session id' in str(e).lower():
            driver.quit()
            driver = init_driver()
            login(driver)
            time.sleep(2)
            #
            menu_search(driver)
            # 페이지 전환 및 로딩 대기 (필요 시 조정)
            time.sleep(2)
            #
            select_categories(driver)
            time.sleep(2)

            return safe_execute_script(driver, script)
        else:
            raise

def main():
    global json_data, saved_count, data_list  # 전역 변수 사용
    driver = init_driver()

    # # 크롬드라이버 화면없이 동작하게 처리하는 방법(배치개념에 적용)
    # chrome_options = Options()
    # chrome_options.add_argument("--headless")
    # chrome_options.add_argument("--disable-gpu")
    # chrome_options.add_argument("--no-sandbox")
    # chrome_options.add_argument("--disable-dev-shm-usage")
    # chrome_options.add_argument("--remote-debugging-port=9222")  # 원격 디버깅 포트
    # chrome_options.add_argument("--disable-background-timer-throttling")
    # chrome_options.add_experimental_option("detach", True)  # 크롬 창을 셀레니움 종료 시 닫지 않음
    # # 필요에 따라 추가 옵션 설정: --no-sandbox, --disable-dev-shm-usage 등
    #
    # driver = webdriver.Chrome()
    try:
        # 시군구등 법정코드 json 데이타 로딩
        json_data = load_json_data()

        # driver = init_driver()
        driver = safe_get(driver, "https://www.tankauction.com/")
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
        time.sleep(1)

        #
        npl_drop_table()

        # 총 건수 가져오기
        total_records = get_total_count(driver)

        # 페이징 이동 및 데이터 처리
        navigate_pages(driver, total_records)

        # 마지막 남은 레코드 저장
        if data_list:
            print(f"마지막 저장 전 현재까지 저장 건수: {saved_count + len(data_list)} 건, 남은 배치: {len(data_list)} 건")
            npl_save_to_sqlite(data_list)
            saved_count += len(data_list)
            data_list.clear()
        print(f"총 저장 건수: {saved_count} 건")
        # 스크립트 종료 전에 현재 sale_edate(현재 날짜)를 파일에 저장
        save_last_sale_date(sale_edate)

    except Exception as e:
        print("오류 발생:", e)
    finally:
        driver.quit()
        # detail_driver.quit()

if __name__ == "__main__":
    main()