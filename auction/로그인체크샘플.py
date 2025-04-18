from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re

try:
    # 크롬 드라이버 생성 (환경 변수 등록되어 있으면 경로 지정 생략 가능)
    driver = webdriver.Chrome()

    # ===== 크롬 드라이버 정상 작동 검증 =====
    driver.get("https://www.google.com")
    if "Google" in driver.title:
        print("Chrome 드라이버가 정상 작동합니다.")
    else:
        print("Chrome 드라이버 작동 테스트 실패: 올바른 페이지가 로드되지 않았습니다.")

    # 타겟 사이트 접속 (tankauction)
    driver.get("https://www.tankauction.com/")
    driver.implicitly_wait(5)

    # 로그인 팝업을 띄우는 버튼 클릭 (onclick="floating_div(400);")
    login_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//*[@onclick='floating_div(400);']"))
    )
    login_button.click()

    # 로그인 팝업이 표시될 때까지 대기 (팝업의 id는 "FLOATING_CONTENT")
    login_popup = WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.ID, "FLOATING_CONTENT"))
    )

    # 디버깅을 위한 로그인 팝업 HTML 출력
    login_html = login_popup.get_attribute("outerHTML")
    print("로그인 팝업의 HTML:")
    print(login_html)

    # 아이디와 비밀번호 입력 필드 선택 (name 속성: client_id, passwd)
    username_field = login_popup.find_element(By.NAME, "client_id")
    password_field = login_popup.find_element(By.NAME, "passwd")

    # 로그인 정보 입력 (실제 계정 정보로 변경)
    username_field.send_keys("wfight69")
    password_field.send_keys("ahdtpddlta_0")

    # 로그인 버튼 클릭 (<a> 태그, onclick="login();")
    submit_button = login_popup.find_element(By.XPATH, ".//a[contains(@onclick, 'login();')]")
    submit_button.click()

    # 로그인 후 추가 작업을 위한 대기 (예: 사용자 페이지 로딩 확인)
    time.sleep(5)
    print("로그인 시도 완료.")

    # ======================================================================
    # "경매검색" 메뉴 클릭 (<a href="/ca/caList.php" ... >경매검색</a> 요소 선택)
    auction_search = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//a[@href='/ca/caList.php' and contains(text(), '경매검색')]"))
    )
    auction_search.click()
    print("경매검색 메뉴 클릭 완료.")

    # 페이지 전환 및 로딩 대기 (필요 시 조정)
    time.sleep(3)

    # ======================================================================
    # [추가] "showCtgrMulti(this)" 버튼 클릭하여 카테고리 선택 창 열기
    category_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//*[@onclick='showCtgrMulti(this)']"))
    )
    category_button.click()
    print("카테고리 선택 창 열기 완료.")

    # 잠시 대기 (모달/드롭다운이 로드될 시간 확보)
    time.sleep(3)

    # ======================================================================
    # [추가] <ul id="ulGrpCtgr_10"> 내에서 "아파트", "연립주택", "다세대주택" 항목 체크
    for category in ["아파트", "연립주택", "다세대주택"]:
        try:
            checkbox = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        f"//*[@id='ulGrpCtgr_10']//span[contains(text(), '{category}')]/preceding-sibling::input[@type='checkbox']"
                    )
                )
            )
            if not checkbox.is_selected():
                checkbox.click()
                print(f"'{category}' 체크박스 선택됨.")
        except Exception as e:
            print(f"'{category}' 체크박스 선택 중 오류 발생:", e)

    # ======================================================================
    # [추가] <ul id="ulGrpCtgr_20"> 내에서 "근린생활시설"과 "근린상가" 항목 체크
    for category in ["근린생활시설", "근린상가"]:
        try:
            checkbox = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        f"//*[@id='ulGrpCtgr_20']//span[contains(text(), '{category}')]/preceding-sibling::input[@type='checkbox']"
                    )
                )
            )
            if not checkbox.is_selected():
                checkbox.click()
                print(f"'{category}' 체크박스 선택됨.")
        except Exception as e:
            print(f"'{category}' 체크박스 선택 중 오류 발생:", e)

    # 잠시 대기 (모달/드롭다운이 로드될 시간 확보)
    time.sleep(3)

    # ======================================================================
    # 검색 처리: srchClick() 함수 실행 (검색결과 로드)
    driver.execute_script("srchClick();")
    print("srchClick() 함수 실행 완료.")

    # 결과가 로드될 때까지 대기 (#lsTbody 요소가 로드되길 기다림)
    tbody = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#lsTbody"))
    )
    # tbody 안의 모든 tr 요소 선택
    rows = tbody.find_elements(By.TAG_NAME, "tr")

    print("목록 항목 수:", len(rows))
    print("목록 정보 출력:")

    # 각 행마다 순번번호를 앞에 출력하면서 정보 추출 및 텍스트 내용 출력
    for idx, row in enumerate(rows, start=1):
        try:
            # 1. 건물 전용면적 추출 (예: .blue.f12 요소의 텍스트)
            area_element = row.find_element(By.CSS_SELECTOR, ".blue.f12")
            area_text = area_element.text.strip()
            # 첫 부분(쉼표 기준)에서 면적 추출 (정규표현식: 괄호 안의 숫자. 예: (52.3평))
            text_parts = area_text.split(',')
            regex = r"\((\d+\.\d+)\s*평\)"
            match = re.search(regex, text_parts[0])
            if match:
                area_py = float(match.group(1))
            else:
                print(f"{idx}번 항목: 면적 정보 없음 - pass")
                continue

            # 2. 금액1 추출 ([id^="apslAmt_"])
            price1_element = row.find_element(By.CSS_SELECTOR, "[id^='apslAmt_']")
            price1_text = price1_element.text.strip().replace(",", "")
            price1_num = int(price1_text) if price1_text.isdigit() else 0

            # 3. 금액2 추출 ([id^="minbAmt"])
            price2_element = row.find_element(By.CSS_SELECTOR, "[id^='minbAmt']")
            price2_text = price2_element.text.strip().replace(",", "")
            price2_num = int(price2_text) if price2_text.isdigit() else 0

            # 4. 전용면적 대비 단가 계산 (만원 단위)
            if area_py != 0:
                pydanga1 = int(price1_num / (area_py * 10000))
                pydanga2 = int(price2_num / (area_py * 10000))
            else:
                pydanga1 = pydanga2 = 0

            # 순번번호와 함께 각 행의 정보 출력
            print(
                f"{idx}. 면적: {area_py}평, 금액1: {price1_num}, 금액2: {price2_num} -> 단가1: {pydanga1}만원, 단가2: {pydanga2}만원")
            print("관련 내용:")
            print(row.text)
            print("-" * 80)
        except Exception as inner_e:
            print(f"{idx}번 항목 처리 중 오류 발생: {inner_e}")

except Exception as e:
    print("오류 발생:", e)

finally:
    driver.quit()
