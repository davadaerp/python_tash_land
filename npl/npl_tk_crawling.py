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

from auction.auction_geocode_utils import is_valid_latlng, retry_geocode_failed_address
from common.vworld_utils import VWorldGeocoding
from jumpo.jumpo_crawling import detail_driver
#
from npl_db_utils import npl_save_to_sqlite, npl_drop_table
from config import NPL_DB_PATH, MAP_API_KEY, VWORLD_URL
from pubdata.public_land_lawd_code_db_utils import get_lawd_by_name

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

# 테스트용: "Y"이면 첫 페이지(page_list=100)만 처리 후 종료
#           "N"이면 전체 페이지 계속 처리
PAGE_TEST_YN = "Y"

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
    # 2. 진행물건 옵션 선택 (DOM 속성을 직접 제어하여 disabled 해제 및 value 부여)
    try:
        stat_select = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "stat"))
        )
        # JavaScript를 사용하여 '매각전부' 옵션 수정 (비활성화 해제 및 value 설정)
        driver.execute_script("""
            let option = [...document.querySelectorAll("#stat option")].find(opt => opt.textContent.includes("진행물건"));
            if (option) {
                option.removeAttribute("disabled");
                option.classList.remove("bg_gray");
                option.setAttribute("value", "11");
            }
        """)
        # Select 객체를 사용하여 수정된 옵션 선택
        select_obj = Select(stat_select)
        select_obj.select_by_value("11")         # 진행물건(11), 매각전부(12)

        print("진행전부 옵션 선택됨.")
        time.sleep(2)
    except Exception as e:
        print("진행전부 옵션 선택 중 오류 발생:", e)

    # ======================================================================
    # 3-1. 주거용 카테고리 체크박스 선택
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


    # 3-2. 상업 및 산업용 등 기타 카테고리 체크박스 선택
    try:
        commercial_checkbox = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.ID, "chkGrpCtgr_20")
            )
        )

        if not commercial_checkbox.is_selected():
            driver.execute_script("arguments[0].click();", commercial_checkbox)

        print("상업 및 산업용 전체 선택 완료")

    except Exception as e:
        print("상업 및 산업용 선택 실패:", e)

    # ======================================================================
    # 4. 첫 번째 검색 실행 (총 건수 확인을 위함)
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
    # 5. 검색 목록수를 설정값(page_list)으로 변경
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
    print("📌 record_parsing_list() 호출됨, 현재 페이지:", current_page)
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
        tid = row.get_attribute("data-tid")

        # print(f"{idx}: tid = {tid}")
        npl_info = npl_extract_info(driver, row_text, tid)
        if npl_info is None:
            continue  # NPL 아님, 다음 로우로

        # info 언패킹
        #deposit_value, min_price, bond_max_amount, bond_claim_amount, start_decision_date, auction_method, auction_applicant, notice_text = npl_info

        # 상세정보 처리
        print(f"📌 상세정보(좌표구하기등) 처리 시작: TID {tid}")
        extract_info(row_text, npl_info)

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

            # ============================================================
            # 테스트 모드
            # Y : 첫 페이지(page_list 개수) 처리 후 종료
            # N : 기존처럼 전체 페이지 계속 처리
            # ============================================================
            if PAGE_TEST_YN.upper() == "Y":
                print(
                    f"🧪 테스트 모드 종료: "
                    f"첫 페이지 {page_list}개 목록 처리 후 페이징을 종료합니다."
                )
                break

        except WebDriverException as e:
            print("WebDriver error, retrying page:", e)
            # (위 safe_execute_script가 이미 재시작까지 처리해 줍니다)
            continue
        # except Exception as e:
        #     print("❌ 페이지 이동 중 오류 발생 또는 마지막 페이지 도달:", e)
        #     break

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
        #print("📌 npl_extract_info() 호출됨, TID:", tid)
        lines = row_text.split('\n')

        #print('== row_text: ' + row_text)

        # ============================================================
        # 감정가 / 최저가 / 유찰횟수 / 낙찰비율 / 매각기일 추출
        # 목록 중간에 공매정보, 평당금액 등이 추가되어도
        # 고정 줄번호를 사용하지 않고 실제 데이터 형식으로 추출
        # ============================================================
        appraisal_price = '0'
        min_price = '0'
        bid_count = '0'
        bid_rate = '0'
        sale_decision_date_text = ''
        sale_decision_date = ''

        # ------------------------------------------------------------
        # 1. 독립된 금액 라인 추출
        #
        # 예:
        # 437,751,620
        # 214,498,000
        #
        # "(토지) 평당 154만"
        # "공매 ... (감정: 120,000,000 / 최저: ...)"
        # 등의 금액은 제외
        # ------------------------------------------------------------
        price_list = []

        for line in lines:
            line = line.strip()

            # 한 줄 전체가 금액인 경우만 인정
            if re.fullmatch(r'\d{1,3}(?:,\d{3})+', line):
                price_list.append(line)

        # 첫 번째 금액 = 감정평가금액
        if len(price_list) >= 1:
            appraisal_price = price_list[0]

        # 두 번째 금액 = 최저낙찰가
        if len(price_list) >= 2:
            min_price = price_list[1]

        # ------------------------------------------------------------
        # 2. 유찰횟수 추출
        #
        # 예:
        # 유찰 3회
        # → 3
        # ------------------------------------------------------------
        for line in lines:
            line = line.strip()

            bid_count_match = re.search(r'유찰\s*(\d+)\s*회', line)

            if bid_count_match:
                bid_count = bid_count_match.group(1)
                break

        # ------------------------------------------------------------
        # 3. 낙찰비율 추출
        #
        # 예:
        # (34%)
        # → 34%
        # ------------------------------------------------------------
        for line in lines:
            line = line.strip()

            bid_rate_match = re.fullmatch(r'\(\s*(\d+)%\s*\)', line)

            if bid_rate_match:
                bid_rate = bid_rate_match.group(1) + '%'
                break

        # ------------------------------------------------------------
        # 4. 매각기일 추출
        #
        # 예:
        # 26.10.01
        # → 2026-10-01
        # ------------------------------------------------------------
        for line in lines:
            line = line.strip()

            if re.fullmatch(r'\d{2}\.\d{2}\.\d{2}', line):
                sale_decision_date_text = line
                break

        if sale_decision_date_text:
            sale_decision_date = convert_to_iso(
                sale_decision_date_text
            )

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

        # print("📌 채권합계금액:", bond_total_amount)

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

        print('-')
        print('== TID: ' + tid )
        print('== 감정평가금액: ' + appraisal_price)
        print('== 최저낙찰가:  ' + min_price)
        print('== 최저유찰회수: ' + bid_count)
        print('== 낙찰비율: ' + bid_rate)
        print('== 매각일자: ' + sale_decision_date)
        print("📌 채권합계금액:", bond_total_amount)
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


# 주소로 시군구 데이타 파싱및 분석
def extract_info(row_text, npl_info):
    try:
        print("📌 상세정보 처리 시작: TID", npl_info[-1])
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
            print(f"금액 파싱 오류 : {e}")


        # 판매금액및 비율 정보 추출
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

        # 판매금액및 비율 정보 추출
        # sale_price = 0

        # 임의경매신청자가 개인인경우(default N)
        # 한글 3자이며 '신협', '금고', '은행' 포함하지 않을 경우 'Y', 아니면 'N'
        if (
                re.fullmatch(r'[가-힣]{3}', auction_applicant) and
                not any(keyword in auction_applicant for keyword in ['신협', '금고', '은행'])
        ):
            personal_status = 'Y'
        else:
            personal_status = 'N'


        # ------------------------------------------------------------
        # 11. 법정동 코드
        region = ""
        lawd_cd = ""
        lawd_name = ""
        sigungu_code = ""
        sigungu_name = ""
        umd_name = ""

        # 필요시 다시 활성화
        try:

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
            print(f"📌 주소로부터 지역 정보 추출 시도: {address1}")
            row = get_lawd_by_name(address1)

            lawd_cd = row.get("lawd_cd", "")
            lawd_name = row.get("lawd_name", "")
            region = row.get("region", "")
            sigungu_code = row.get("sigungu_code", "")
            sigungu_name = row.get("sigungu_name", "")
            umd_name = row.get("umd_name", "")
        except Exception as e:
            print(f"법정동 코드 파싱 오류 : {e}")

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
                f"좌표 변환 오류: {e}"
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
            "lawd_cd": lawd_cd,
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
    global saved_count, data_list  # 전역 변수 사용

    # # 크롬드라이버 화면없이 동작하게 처리하는 방법(배치개념에 적용)
    driver = create_driver()
    try:
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