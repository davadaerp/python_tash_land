from selenium import webdriver
from selenium.common import StaleElementReferenceException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import time
import re
import json
import os

from webdriver_manager.chrome import ChromeDriverManager

from jumpo.jumpo_crawling import detail_driver
#
from npl_db_utils import npl_save_to_sqlite
from config import NPL_DB_PATH

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
#BATCH_SIZE = 500     # 레코드 1000건마다 저장
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
    # 상업및 산업용 체크박스 선택처리
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


# tid번호를 이용한 npl여부츨 체크함
def npl_extract_info(driver, tid):
    try:
        #
        appraisal_price = "3,030,768,000"  # 감정금액
        min_price = "1,039,553,000"  # 최저금액
        bid_count = "유찰 3회" # 유찰회수
        bid_rate = "34%"
        sale_decision_date = '2025-06-11'  # 매각기일
        print('-')
        print('== tid: ' + tid )
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
        return deposit_value, bond_total_amount, appraisal_price, min_price, bid_count, bid_rate, bond_max_amount, bond_claim_amount, start_decision_date, sale_decision_date, auction_method, auction_applicant, notice_text, opposability_status

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



def main():
    global json_data, saved_count, data_list  # 전역 변수 사용
    global detail_driver

    # 크롬드라이버 화면없이 동작하게 처리하는 방법(배치개념에 적용)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--remote-debugging-port=9222")  # 원격 디버깅 포트
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_experimental_option("detach", True)  # 크롬 창을 셀레니움 종료 시 닫지 않음
    # 필요에 따라 추가 옵션 설정: --no-sandbox, --disable-dev-shm-usage 등

    # from selenium.webdriver.chrome.service import Service
    # driver = webdriver.Chrome(
    #     service=Service(ChromeDriverManager().install()),
    #     options=chrome_options
    # )
    driver = webdriver.Chrome()
    try:
        #
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
        time.sleep(1)

        # 총 건수 가져오기
        total_records = get_total_count(driver)

        # print(f"{idx}: tid = {tid}")
        tid = '2248276'
        npl_info = npl_extract_info(driver, tid)
        if npl_info is None:
            return  # NPL 아님, 다음 로우로

    except Exception as e:
        print("오류 발생:", e)
    finally:
        driver.quit()
        # detail_driver.quit()

if __name__ == "__main__":
    main()