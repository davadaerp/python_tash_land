import requests
from selenium import webdriver
from selenium.webdriver import ActionChains
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

# ------------------------------
# 스크립트 시작 시 현재 날짜 기준으로 sale_edate를 설정하고,
# sale_sdate 는 DB에 저장된 마지막 crawling_last_date 를 기준으로 가져옵니다.
today = datetime.today().strftime("%Y-%m-%d")
sale_sdate = auction_get_last_crawling_final_date()
sale_edate = today
# ------------------------------

# 저장 방식 선택: "csv" 또는 "sqlite"
SAVE_MODE = "sqlite"  # 원하는 방식으로 변경 가능 (예: "csv")
BATCH_SIZE = 500     # 레코드 1000건마다 저장

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
        # 1. 메인 화면의 로그인 버튼 클릭
        # (data-action="loginDivBtn" 속성을 가진 span 태그를 찾습니다)
        login_open_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "span[data-action='loginDivBtn']"))
        )
        login_open_btn.click()

        # 2. 로그인 팝업이 나타날 때까지 대기
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "FLOATING_CONTENT"))
        )

        # 3. 아이디 및 비밀번호 입력
        # 팝업 내부에 있으므로 driver에서 바로 찾아도 무방합니다 (ID가 유니크함)
        username_field = driver.find_element(By.ID, "client_id")
        password_field = driver.find_element(By.ID, "passwd")

        username_field.clear()  # 기존 입력값이 있을 수 있으므로 초기화
        username_field.send_keys("wfight69")

        password_field.clear()
        password_field.send_keys("ahdtpddldi#$0")

        # 4. 로그인 버튼 클릭
        # HTML상에 id="loginBtn"인 버튼이 존재합니다.
        submit_button = driver.find_element(By.ID, "loginBtn")
        submit_button.click()

        print("로그인 시도 완료.")

    except Exception as e:
        print(f"로그인 오류 발생: {e}")

# 메뉴처리
def menu_search(driver):
    try:
        wait = WebDriverWait(driver, 10)

        # 1. "경매검색" 메인 메뉴 클릭
        main_menu = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//li/a[contains(text(), '경매검색')]"))
        )
        driver.execute_script("arguments[0].click();", main_menu)
        print("경매검색 메뉴 클릭 완료.")

        # 1초 대기 후 종합검색 클릭
        time.sleep(1)

        # 2. 하위 메뉴 중 "종합검색" 클릭
        # sub_menu_total = wait.until(
        #     EC.element_to_be_clickable((By.XPATH, "//ul[contains(@class,'drop_down')]//a[normalize-space()='종합검색']"))
        # )
        # driver.execute_script("arguments[0].click();", sub_menu_total)
        # print("종합검색 메뉴 클릭 완료.")

    except Exception as e:
        print("경매검색/종합검색 메뉴 선택 오류:", e)


def select_categories(driver):
    wait = WebDriverWait(driver, 10)

    # ======================================================================
    # 1. 물건용도 선택 펼치기
    # 현재 HTML 기준:
    # - 버튼: id="btn_power"
    # - 펼쳐지는 영역: id="trCtgrMulti"
    try:
        btn_power = wait.until(
            EC.presence_of_element_located((By.ID, "btn_power"))
        )

        tr_ctgr_multi = wait.until(
            EC.presence_of_element_located((By.ID, "trCtgrMulti"))
        )

        # 접혀 있으면 펼치기
        # data-state="1" 이면 현재 펼쳐진 상태로 보이므로,
        # style / 표시상태를 같이 확인해서 안정적으로 처리
        is_hidden = not tr_ctgr_multi.is_displayed()

        if is_hidden:
            driver.execute_script("arguments[0].click();", btn_power)
            print("물건용도 선택 펼치기 완료.")
            time.sleep(1)
        else:
            print("물건용도 선택은 이미 펼쳐진 상태입니다.")
    except Exception as e:
        print("물건용도 선택 펼치기 중 오류 발생:", e)

    # ======================================================================
    # 2. 전체보기 체크 해제
    # 현재 구조상 chkAllCtgr 가 기본 checked 상태일 수 있으므로,
    # 개별 카테고리만 적용하려면 먼저 해제하는 것이 안전함.
    # try:
    #     chk_all = wait.until(
    #         EC.presence_of_element_located((By.ID, "chkAllCtgr"))
    #     )
    #     if chk_all.is_selected():
    #         driver.execute_script("arguments[0].click();", chk_all)
    #         print("전체보기 체크 해제 완료.")
    #         time.sleep(0.5)
    # except Exception as e:
    #     print("전체보기 체크 해제 중 오류 발생:", e)

    # ======================================================================
    # 5. 주거용 카테고리 선택
    residential_categories = [
        "아파트",
        "연립주택",
        "다세대주택",
        "오피스텔(주거)",
        "단독주택",
        "다가구주택",
        "도시형생활주택",
        "상가주택",
    ]

    for category in residential_categories:
        try:
            checkbox = wait.until(
                EC.presence_of_element_located((
                    By.XPATH,
                    f"//*[@id='ulGrpCtgr_10']//input[@type='checkbox' and @data-ment='{category}']"
                ))
            )

            if not checkbox.is_selected():
                driver.execute_script("arguments[0].click();", checkbox)
                print(f"주거용 카테고리 선택됨: {category}")
                time.sleep(0.2)
            else:
                print(f"주거용 카테고리 이미 선택됨: {category}")

        except Exception as e:
            print(f"주거용 카테고리 선택 오류 ({category}):", e)

    # ======================================================================
    # 6. 상업 및 산업용 카테고리 선택
    commercial_categories = [
        "근린생활시설",
        "근린상가",
        "숙박시설",
        "업무시설",
        "공장",
        "지식산업센터",
        "교육연구시설",
        "창고시설",   # HTML 실제 명칭 기준
    ]

    for category in commercial_categories:
        try:
            checkbox = wait.until(
                EC.presence_of_element_located((
                    By.XPATH,
                    f"//*[@id='ulGrpCtgr_20']//input[@type='checkbox' and @data-ment='{category}']"
                ))
            )

            if not checkbox.is_selected():
                driver.execute_script("arguments[0].click();", checkbox)
                print(f"상업/산업용 카테고리 선택됨: {category}")
                time.sleep(0.2)
            else:
                print(f"상업/산업용 카테고리 이미 선택됨: {category}")

        except Exception as e:
            print(f"상업/산업용 카테고리 선택 오류 ({category}):", e)

    # ======================================================================
    # 3. 매각기일 설정
    try:
        wait = WebDriverWait(driver, 10)

        bgnDt = wait.until(
            EC.presence_of_element_located((By.ID, "bgnDt"))
        )
        endDt = wait.until(
            EC.presence_of_element_located((By.ID, "endDt"))
        )

        # type="date" 는 yyyy-mm-dd 형식이어야 함
        sale_sdate_iso = sale_sdate.strip()  # 예: 2026-04-15
        sale_edate_iso = sale_edate.strip()  # 예: 2026-04-15

        driver.execute_script("""
            const setDateValue = (el, value) => {
                el.removeAttribute('readonly');
                el.value = value;
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
            };

            setDateValue(arguments[0], arguments[1]);
            setDateValue(arguments[2], arguments[3]);
        """, bgnDt, sale_sdate_iso, endDt, sale_edate_iso)

        time.sleep(0.5)

        bgn_val = bgnDt.get_attribute("value")
        end_val = endDt.get_attribute("value")

        print(f"매각기일 설정 완료: 시작={bgn_val}, 종료={end_val}")

        # 값 검증
        if bgn_val != sale_sdate_iso or end_val != sale_edate_iso:
            print("매각기일 입력값이 기대값과 다릅니다. DOM 재확인 필요.")
        else:
            print("매각기일 값 반영 정상.")

        time.sleep(1)

    except Exception as e:
        print("매각기일 설정 중 오류 발생:", e)

    # ======================================================================
    # 4. 진행상태: 매각전부 선택
    try:
        stat_select = wait.until(
            EC.presence_of_element_located((By.ID, "stat"))
        )
        Select(stat_select).select_by_value("12")
        print("진행상태 '매각전부' 선택 완료.")

        time.sleep(1)
    except Exception as e:
        print("진행상태 '매각전부' 선택 중 오류 발생:", e)


    # ======================================================================
    # 7. 첫 검색 실행
    # try:
    #     driver.execute_script("srchClick();")
    #     print("srchClick() 검색 실행 완료.")
    # except Exception as e:
    #     print("srchClick() 실행 중 오류 발생:", e)
    #     return

    # 결과 로드 대기
    try:
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#lsTbody"))
        )
        print("검색 결과 로드 완료.")

        time.sleep(1)
    except Exception as e:
        print("검색 결과 로드 대기 중 오류 발생:", e)

    # ======================================================================
    # 8. 목록수 설정
    # 첨부 HTML 하단 결과 목록 select는 id="dataSize" 임
    set_page_list_size(driver)

    time.sleep(3)


# page설정
def set_page_list_size(driver, page_list="100"):
    try:
        wait = WebDriverWait(driver, 10)

        # 결과 목록 개수 select
        data_size_select = wait.until(
            EC.presence_of_element_located((By.ID, "dataSize"))
        )

        current_value = data_size_select.get_attribute("value")
        if str(current_value) != str(page_list):
            Select(data_size_select).select_by_value(str(page_list))
            print(f"목록수 {page_list}개씩 보기 설정 완료.")

            # 목록 재로딩 대기
            wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#lsTbody tr.listToggle[data-tid]"))
            )
            time.sleep(1)
        else:
            print(f"목록수는 이미 {page_list}개씩 보기로 설정되어 있습니다.")

        # 실제 반영된 값 다시 확인
        data_size_select = wait.until(
            EC.presence_of_element_located((By.ID, "dataSize"))
        )
        applied_value = data_size_select.get_attribute("value")

        # ======================= 🔥 추가 시작 =======================
        total_count = get_total_count(driver)
        print(f"📊 전체건수: {total_count}건 / 현재 목록수: {applied_value}건")
        # ======================= 🔥 추가 끝 =======================

        return int(applied_value)

    except Exception as e:
        print("목록수 설정 중 오류 발생:", e)
        return 20


# ======================================================================
# 총건수 가져오기 함수
# ======================================================================
def get_total_count(driver):
    try:
        total_count_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "totalCnt"))
        )

        raw_text = total_count_element.text.strip()   # 예: "309"
        number_text = re.sub(r"[^\d]", "", raw_text)  # 숫자만 추출

        total_count = int(number_text) if number_text else 0
        print(f"🔹 총 검색된 물건 수: {total_count} 건")
        return total_count

    except Exception as e:
        print("총건수 가져오기 오류:", e)
        return 0

# ======================================================================
# 페이징 이동 및 데이터 처리
# ======================================================================
def navigate_pages(driver, total_records):
    wait = WebDriverWait(driver, 10)
    total_pages = (total_records // int(page_list)) + (1 if total_records % int(page_list) > 0 else 0)
    visited_pages = set()

    def wait_list_reload():
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#lsTbody tr.listToggle[data-tid]"))
        )
        time.sleep(1)

    def get_current_page_from_paging():
        try:
            paging = wait.until(
                EC.presence_of_element_located((By.ID, "paging"))
            )
            strong = paging.find_element(By.TAG_NAME, "strong")
            return int(strong.text.strip())
        except Exception:
            return 1

    def click_page_number(target_page):
        """
        현재 paging 영역에서 target_page 숫자 버튼이 보이면 클릭하고 True 반환
        없으면 False 반환
        """
        try:
            paging = wait.until(
                EC.presence_of_element_located((By.ID, "paging"))
            )
            page_buttons = paging.find_elements(By.CSS_SELECTOR, "div.pageBtn")

            for btn in page_buttons:
                txt = btn.text.strip()
                if txt == str(target_page):
                    driver.execute_script("arguments[0].click();", btn)
                    return True

            return False
        except Exception:
            return False

    def click_next_group():
        """
        paging 영역에서 '다음' 버튼 클릭
        """
        try:
            paging = wait.until(
                EC.presence_of_element_located((By.ID, "paging"))
            )
            page_buttons = paging.find_elements(By.CSS_SELECTOR, "div.pageBtn")

            for btn in page_buttons:
                txt = btn.text.strip()
                if txt == "다음":
                    driver.execute_script("arguments[0].click();", btn)
                    return True

            return False
        except Exception:
            return False

    for page_no in range(1, total_pages + 1):
        try:
            print(f"\n📌 {page_no}/{total_pages} 페이지 이동 중...")

            if page_no in visited_pages:
                print(f"✅ {page_no} 페이지는 이미 방문하여 스킵.")
                continue

            current_page = get_current_page_from_paging()

            # 첫 페이지는 이미 열려 있을 수 있음
            if page_no == 1 and current_page == 1:
                print("현재 1페이지 상태이므로 바로 파싱합니다.")
                record_parsing_list(driver, page_no)
                visited_pages.add(page_no)
                continue

            # 목표 페이지가 현재 paging DOM에 보일 때까지 다음 그룹 이동
            guard = 0
            while True:
                guard += 1
                if guard > 2000:
                    raise Exception(f"{page_no} 페이지 탐색 중 무한루프 방지 종료")

                if click_page_number(page_no):
                    break

                moved = click_next_group()
                if not moved:
                    raise Exception(f"{page_no} 페이지 버튼 또는 '다음' 버튼을 찾지 못했습니다.")

                time.sleep(2)

            # 페이지 이동 후 재로딩 대기
            wait_list_reload()

            # 현재 페이지 확인
            moved_page = get_current_page_from_paging()
            print(f"현재 이동된 페이지: {moved_page}")

            # 레코드 파싱
            record_parsing_list(driver, page_no)
            visited_pages.add(page_no)

        except Exception as e:
            print("❌ 페이지 이동 중 오류 발생 또는 마지막 페이지 도달:", e)
            break

# ======================================================================
# 레코드 데이타 처리
# 결과가 로드될 때까지 대기 (#lsTbody 요소가 로드되길 기다림)
# ======================================================================
def record_parsing_list(driver, current_page):
    global saved_count, data_list

    try:
        tbody = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#lsTbody"))
        )

        # 실제 물건 행만 선택
        rows = tbody.find_elements(By.CSS_SELECTOR, "tr.listToggle[data-tid]")

        row_count = len(rows)
        if row_count == 0:
            print(f"⚠️ 현재 페이지({current_page})에서 파싱할 레코드가 없습니다.")
            return

        for idx, row in enumerate(rows, start=1):
            try:
                extract_info(driver, row, idx)

                # 배치 저장 처리
                if len(data_list) >= BATCH_SIZE:
                    print(f"저장 전 현재까지 저장 건수: {saved_count + len(data_list)} 건, 이번 배치: {len(data_list)} 건")
                    auction_save_to_sqlite(data_list)
                    saved_count += len(data_list)
                    data_list.clear()
                    time.sleep(1)

            except Exception as row_e:
                print(f"행 파싱 오류 (페이지:{current_page}, idx:{idx}): {row_e}")

        total_parsed = (current_page - 1) * int(page_list) + row_count
        print(f"📄 현재 페이지: {current_page}, 현재목록 수: {row_count}, 현재까지 읽은 목록 수: {total_parsed}")

    except Exception as e:
        print("record_parsing_list 오류:", e)


# 주소로 시군구 데이타 파싱및 분석
def extract_info(driver, row, idx):
    try:
        tid = row.get_attribute("data-tid")
        if not tid:
            print(f"idx={idx} : data-tid 없음, 스킵")
            return

        # ------------------------------------------------------------
        # 내부 유틸
        def safe_text(el, selector, default=""):
            try:
                return el.find_element(By.CSS_SELECTOR, selector).text.strip()
            except Exception:
                return default

        def safe_attr(el, selector, attr_name, default=""):
            try:
                return el.find_element(By.CSS_SELECTOR, selector).get_attribute(attr_name) or default
            except Exception:
                return default

        def only_number(text, to_int=True):
            txt = (text or "").strip()
            # *** 같이 가려진 값이면 0 처리
            if "*" in txt:
                return 0 if to_int else ""
            num = re.sub(r"[^\d]", "", txt)
            if not num:
                return 0 if to_int else ""
            return int(num) if to_int else num

        def clean_case_number(text):
            text = text or ""

            # (29) 같은 숫자 괄호 제거
            text = re.sub(r"\(\d+\)", "", text)

            # "지도 보기" 제거
            text = text.replace("지도 보기", "")

            # 줄바꿈 제거
            text = text.replace("\n", " ")

            return text.strip()

        def clean_percent(text):
            # "(70%)" -> "70%"
            txt = (text or "").strip()
            if "*" in txt:
                return ""
            m = re.search(r"(\d+)%", txt)
            return f"{m.group(1)}%" if m else ""

        # ------------------------------------------------------------
        # td 구조
        tds = row.find_elements(By.TAG_NAME, "td")
        if len(tds) < 6:
            print(f"idx={idx}, tid={tid} : td 개수 부족({len(tds)})")
            return

        info_td = tds[2]         # 관할법원/소재지/면적
        amount_td = tds[3]       # 감정가/최저가/낙찰가
        status_td = tds[4]       # 진행상태/퍼센트
        bid_td = tds[5]          # 법원/매각일/시간
        views_td = tds[6] if len(tds) > 6 else None  # 조회수

        # ------------------------------------------------------------
        # 1. 기본 정보
        category = safe_text(info_td, f"#{'ctgr_' + tid}", "")
        case_number_raw = safe_text(info_td, f"#{'saNo_' + tid}", "")
        case_number = clean_case_number(case_number_raw)

        # 숨김 주소
        address1 = safe_text(info_td, f"#{'adrs_' + tid}", "")

        # 본문 주소 + 도로명주소
        address2 = ""
        full_address_block = safe_text(info_td, "div.bold_500.black", "")
        if full_address_block:
            lines = [x.strip() for x in full_address_block.split("\n") if x.strip()]
            # 첫 줄은 일반 주소, 둘째 줄은 도로명 주소
            if not address1 and len(lines) >= 1:
                address1 = lines[0]
            if len(lines) >= 2:
                address2 = re.sub(r"[()]", "", lines[1]).strip()

        # ------------------------------------------------------------
        # 2. 금액
        appraisal_price = only_number(safe_text(amount_td, f"#{'apslAmt_' + tid}", "0"), to_int=True)
        min_price = only_number(safe_text(amount_td, f"#{'minbAmt_' + tid}", "0"), to_int=True)
        sale_price = only_number(safe_text(amount_td, f"#{'sucbAmt_' + tid}", "0"), to_int=True)

        # ------------------------------------------------------------
        # 3. 진행상태 / 퍼센트
        stat_name = safe_text(status_td, f"#{'statNm_' + tid}", "")

        status_divs = status_td.find_elements(By.TAG_NAME, "div")
        min_percent = ""
        sale_percent = ""

        percent_candidates = []
        for div in status_divs:
            txt = div.text.strip()
            if "%" in txt:
                percent_candidates.append(txt)

        if len(percent_candidates) >= 1:
            min_percent = clean_percent(percent_candidates[0])
        if len(percent_candidates) >= 2:
            sale_percent = clean_percent(percent_candidates[1])

        # ------------------------------------------------------------
        # 4. 법원 / 매각기일 / 시간
        bid_divs = bid_td.find_elements(By.TAG_NAME, "div")
        court_name = bid_divs[0].text.strip() if len(bid_divs) >= 1 else ""
        bid_date_raw = safe_text(bid_td, f"#{'bidDt_' + tid}", "")
        bid_time = bid_divs[2].text.strip() if len(bid_divs) >= 3 else ""

        sales_date = ""
        if bid_date_raw:
            m = re.search(r"(\d{2})\.(\d{2})\.(\d{2})", bid_date_raw)
            if m:
                yy, mm, dd = m.groups()
                sales_date = f"20{yy}-{mm}-{dd}"

        # ------------------------------------------------------------
        # 5. 면적
        building_m2 = ""
        building_py = ""
        land_m2 = ""
        land_py = ""
        area_py = 0.0

        gray_f12_divs = info_td.find_elements(By.CSS_SELECTOR, "div.gray.f12")
        area_text = ""
        for div in gray_f12_divs:
            txt = div.text.strip()
            if "건물" in txt and ("대지권" in txt or "토지" in txt):
                area_text = txt.replace("\n", " ")
                break

        if area_text:
            bm = re.search(r"건물\s*([\d\.]+)㎡\(([\d\.]+)평\)", area_text)
            lm = re.search(r"(?:대지권|토지)\s*([\d\.]+)㎡\(([\d\.]+)평\)", area_text)

            if bm:
                building_m2, building_py = bm.groups()
                try:
                    area_py = float(building_py)
                except Exception:
                    area_py = 0.0

            if lm:
                land_m2, land_py = lm.groups()

        # ------------------------------------------------------------
        # 6. 특이사항
        special_text = ""
        try:
            special_text = info_td.find_element(By.CSS_SELECTOR, "span.orange").text.strip()
        except Exception:
            special_text = ""

        # ------------------------------------------------------------
        # 7. 조회수
        view_count = 0
        if views_td is not None:
            try:
                view_text = views_td.text.strip()
                view_count = only_number(view_text, to_int=True)
            except Exception:
                view_count = 0

        # ------------------------------------------------------------
        # 8. 이미지 URL
        image_url = safe_text(row, f"#{'imgUrl_' + tid}", "")
        img_src = safe_attr(row, "img.org_viewimg.image", "src", "")

        # ------------------------------------------------------------
        # 9. 평단가 계산
        if area_py and area_py != 0:
            pydanga_appraisal = int(appraisal_price / (area_py * 10000)) if appraisal_price else 0
            pydanga_min = int(min_price / (area_py * 10000)) if min_price else 0
            pydanga_sale = int(sale_price / (area_py * 10000)) if sale_price else 0
        else:
            pydanga_appraisal = 0
            pydanga_min = 0
            pydanga_sale = 0

        # ------------------------------------------------------------
        # 10. 동 / 층 / 단지명
        building, floor, dangi_name = extract_building_floor(address1)

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
            sigungu_code = region_info.get("sigungu_code", "")
            sigungu_name = region_info.get("sigungu_name", "")
            umd_name = region_info.get("umd_name", "")
        except Exception as e:
            print(f"법정동 코드 파싱 오류 idx={idx}: {e}")

        # ------------------------------------------------------------
        # 12. 위도 / 경도
        latitude = "0"
        longitude = "0"

        # 필요시 다시 활성화
        # param address_type: 주소 타입 ("parcel": 지번 [기본값], "road": 도로명)
        try:
            geo_service = VWorldGeocoding(MAP_API_KEY)
            latitude, longitude = geo_service.get_lat_lng(address2, "road")
        except Exception as e:
            print(f"좌표 변환 오류 idx={idx}: {e}")

        # ------------------------------------------------------------
        # 13. 기타정보 묶음
        extra_parts = []
        if court_name:
            extra_parts.append(court_name)
        if bid_time:
            extra_parts.append(bid_time)
        if area_text:
            extra_parts.append(area_text)
        if special_text:
            extra_parts.append(special_text)
        if stat_name:
            extra_parts.append(stat_name)
        if min_percent:
            extra_parts.append(min_percent)
        if sale_percent:
            extra_parts.append(sale_percent)

        extra_info = ", ".join(extra_parts)

        # ------------------------------------------------------------
        # 14. 저장 데이터
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
            "min_percent": min_percent,
            "sale_percent": sale_percent,
            "pydanga_appraisal": f"{pydanga_appraisal}",
            "pydanga_min": f"{pydanga_min}",
            "pydanga_sale": f"{pydanga_sale}",
            "sales_date": sales_date,
            "dangi_name": dangi_name,
            "extra_info": extra_info,
            "latitude": latitude,
            "longitude": longitude,
            "court_name": court_name,
            "bid_time": bid_time,
            "status_name": stat_name,
            "view_count": view_count,
            "image_url": image_url,
            "img_src": img_src,
            "tid": tid
        }

        print(f"[{idx}] 사건번호={data_entry}")

        data_list.append(data_entry)

        # print(
        #     f"[{idx}] 사건번호={case_number}, "
        #     f"구분={category}, "
        #     f"주소={address1}, "
        #     f"감정가={appraisal_price}, "
        #     f"최저가={min_price}, "
        #     f"낙찰가={sale_price}, "
        #     f"상태={stat_name}, "
        #     f"매각일={sales_date}"
        # )

    except Exception as e:
        print(f"데이터 처리 오류 idx={idx}: {e}")


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
    row = get_lawd_by_name(address)

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


def main():
    global json_data, saved_count, data_list  # 전역 변수 사용

    # 크롬드라이버 화면없이 동작하게 처리하는 방법(배치개념에 적용)
    #chrome_options = Options()
    #chrome_options.add_argument("--headless")
    #chrome_options.add_argument("--disable-gpu")
    # 브라우져에서 웹드라이버인지 체크여부(navigator.webdriver 속성 제거)
    #chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    # 필요에 따라 추가 옵션 설정: --no-sandbox, --disable-dev-shm-usage 등

    #driver = webdriver.Chrome(options=chrome_options)
    driver = webdriver.Chrome()
    try:
        driver.get("https://www.dooinauction.com/")
        driver.implicitly_wait(1)
        #=====
        login(driver)
        time.sleep(2)

        # ======================================================================
        # 공지및 기타 팝업메뉴 제거
        #close_popups(driver)

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