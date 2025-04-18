from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import urllib.parse
import pandas as pd
import numpy as np
import re
from selenium.common.exceptions import TimeoutException


def setup_webdriver():
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    return driver


def login(driver, user_id, user_pw):
    # 전자소송포털 로그인 페이지 URL (아이디/패스워드 탭 주소)
    login_url = "https://ecfs.scourt.go.kr/psp/index.on?m=PSP101M01&n=PSP001M01&ak=tANRmaBAZfPto8hcwvaA2gex1PQbxFqUombVC&ru="
    driver.get(login_url)
    wait = WebDriverWait(driver, 50)

    # 예시: 로그인 페이지의 아이디/패스워드 입력 필드 locator (실제 페이지에 맞게 수정 필요)
    try:
        id_field = wait.until(EC.presence_of_element_located((By.ID, user_id)))  # 예시 locator
        pw_field = driver.find_element(By.ID, user_pw)  # 예시 locator
    except TimeoutException:
        print("로그인 입력 필드를 찾지 못했습니다. 페이지 구조를 확인하세요.")
        return

    id_field.clear()
    id_field.send_keys(user_id)
    pw_field.clear()
    pw_field.send_keys(user_pw)

    # 예시: 로그인 버튼 클릭 (실제 locator로 수정)
    try:
        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        login_button.click()
    except Exception as e:
        print("로그인 버튼을 찾지 못했습니다:", e)


def navigate_to_search_page(driver):
    # 로그인 후, 새로운 법원 경매 검색 페이지로 이동 (메인 위치 변경됨)
    new_main_url = "https://www.courtauction.go.kr/pgj/index.on?w2xPath=/pgj/ui/pgj100/PGJ158M00.xml"
    driver.get(new_main_url)
    wait = WebDriverWait(driver, 10)

    # 페이지 구조가 기존과 달라졌을 수 있으므로, 프레임 전환이 필요하지 않다면 아래 코드를 주석 처리합니다.
    # try:
    #     wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "indexFrame")))
    # except TimeoutException:
    #     print("indexFrame 프레임을 찾지 못했습니다. 페이지 구조가 변경되었을 수 있습니다.")

    # 검색 버튼 locator (기존과 동일한 locator를 사용하고 있으나, 실제 페이지에 맞게 수정 필요)
    search_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@id='mf_wfm_mainFrame_btn_dspslRsltSrch']")))
    search_button.click()


def set_search_criteria(driver, input_data, building_codes):
    # 지원 선택 (지원 선택 요소의 id는 'idJiwonNm'로 가정)
    setCourt = Select(driver.find_element(By.ID, 'idJiwonNm'))
    setCourt.select_by_value(input_data['jiwon'])

    # 건물 유형 선택 (하위 분류값 고정)
    setAPT = Select(driver.find_element(By.NAME, 'lclsUtilCd'))
    setAPT.select_by_value("0000802")
    setAPT = Select(driver.find_element(By.NAME, 'mclsUtilCd'))
    setAPT.select_by_value("000080201")
    setAPT = Select(driver.find_element(By.NAME, 'sclsUtilCd'))
    setAPT.select_by_value(building_codes[input_data['building']])

    # 검색 기간 입력
    time_textbox = driver.find_element(By.NAME, 'termStartDt')
    time_textbox.clear()
    time_textbox.send_keys(input_data['start_date'])
    time_textbox = driver.find_element(By.NAME, 'termEndDt')
    time_textbox.clear()
    time_textbox.send_keys(input_data['end_date'])

    # 검색 버튼 클릭
    driver.find_element(By.XPATH, '//*[@id="contents"]/form/div[2]/a[1]/img').click()


def change_items_per_page(driver):
    # 한 페이지당 항목 수 변경 (가능한 경우)
    if driver.find_elements(By.ID, 'ipage'):
        setPage = Select(driver.find_element(By.ID, 'ipage'))
        setPage.select_by_value("default40")
    else:
        driver.find_element(By.XPATH, '//*[@id="contents"]/div[4]/form[1]/div/div/a[4]/img').click()


def extract_table_data(driver):
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    table = soup.find('table', attrs={'class': 'Ltbl_list'})
    table_rows = table.find_all('tr')
    row_list = []
    for tr in table_rows:
        td = tr.find_all('td')
        row = [td_item.text for td_item in td]
        row_list.append(row)
    # 첫 번째 행은 헤더이므로 제외
    return pd.DataFrame(row_list).iloc[1:]


def navigate_pages(driver, aution_item):
    page = 1
    while True:
        aution_item = pd.concat([aution_item, extract_table_data(driver)], ignore_index=True)
        page2parent = driver.find_element(By.CLASS_NAME, 'page2')
        children = page2parent.find_elements(By.XPATH, '*')
        if page == 1:
            if len(children) == page:
                break
            else:
                children[page].click()
        elif page <= 10:
            if len(children) - 1 == page:
                break
            else:
                children[page + 1].click()
        else:
            if len(children) - 2 == (page % 10):
                break
            else:
                children[(page % 10) + 2].click()
        page += 1
    driver.find_element(By.XPATH, '//*[@id="contents"]/div[4]/form[1]/div/div/a[4]/img').click()
    return aution_item


def clean_table_data(aution_item):
    aution_item = aution_item.iloc[:, 1:]
    col_list = ['사건번호', '물건번호', '소재지', '비고', '감정평가액', '날짜']
    aution_item.columns = col_list
    for col in col_list:
        aution_item[col] = aution_item[col].str.replace('\t', '')
        aution_item[col] = aution_item[col].apply(lambda x: re.sub(r"\n+", "\n", x))

    aution_item['법원'] = aution_item['사건번호'].str.split('\n').str[1]
    aution_item['사건번호'] = aution_item['사건번호'].str.split('\n').str[2]
    aution_item['용도'] = aution_item['물건번호'].str.split('\n').str[2]
    aution_item['물건번호'] = aution_item['물건번호'].str.split('\n').str[1]
    aution_item['내역'] = aution_item['소재지'].str.split('\n').str[2:].str.join(' ')
    aution_item['소재지'] = aution_item['소재지'].str.split('\n').str[1]
    aution_item['비고'] = aution_item['비고'].str.split('\n').str[1]
    aution_item['최저가격'] = aution_item['감정평가액'].str.split('\n').str[2]
    aution_item['최저비율'] = aution_item['감정평가액'].str.split('\n').str[3].str[1:-1]
    aution_item['감정평가액'] = aution_item['감정평가액'].str.split('\n').str[1]
    aution_item['유찰횟수'] = aution_item['날짜'].str.split('\n').str[3].str.strip()
    aution_item['유찰횟수'] = np.where(aution_item['유찰횟수'].str.len() == 0, '0회', aution_item['유찰횟수'].str.slice(start=2))
    aution_item['날짜'] = aution_item['날짜'].str.split('\n').str[2]

    aution_item = aution_item[['날짜', '법원', '사건번호', '물건번호', '용도',
                               '감정평가액', '최저가격', '최저비율', '유찰횟수', '소재지', '내역', '비고']]
    aution_item = aution_item[~aution_item['비고'].str.contains('지분매각')].reset_index(drop=True)
    return aution_item


def encode_to_euc_kr_url(korean_text):
    euc_kr_encoded = korean_text.encode('euc-kr')
    return urllib.parse.quote(euc_kr_encoded)


def create_url(row):
    court_name_encoded = encode_to_euc_kr_url(row["법원"])
    sa_year, sa_ser = row["사건번호"].split("타경")
    url = f"https://www.courtauction.go.kr/RetrieveRealEstDetailInqSaList.laf?jiwonNm={court_name_encoded}&saYear={sa_year}&saSer={sa_ser}&_CUR_CMD=InitMulSrch.laf&_SRCH_SRNID=PNO102014&_NEXT_CMD=RetrieveRealEstDetailInqSaList.laf"
    return url


def run_crawling(driver, input_data, building_codes):
    navigate_to_search_page(driver)
    #set_search_criteria(driver, input_data, building_codes)
    change_items_per_page(driver)
    aution_item = pd.DataFrame()
    aution_item = navigate_pages(driver, aution_item)
    aution_item = clean_table_data(aution_item)
    aution_item["URL"] = aution_item.apply(create_url, axis=1)
    driver.quit()
    return aution_item


if __name__ == "__main__":
    # 로그인 정보 정의
    user_id = "wfight69"  # 실제 아이디로 변경
    user_pw = "ahdtpddl#$0"  # 실제 비밀번호로 변경

    # 기본 입력값 설정
    input_data = {
        'jiwon': '서울중앙지방법원',
        'building': '아파트',
        'start_date': '2025.01.01',
        'end_date': '2025.01.31'
    }

    building_codes = {
        "단독주택": "00008020101",
        "다가구주택": "00008020102",
        "다중주택": "00008020103",
        "아파트": "00008020104",
        "연립주택": "00008020105",
        "다세대주택": "00008020106",
        "기숙사": "00008020107",
        "빌라": "00008020108",
        "상가주택": "00008020109",
        "오피스텔": "00008020110",
        "주상복합": "00008020111"
    }

    print("크롤링을 시작합니다...\n")
    driver = setup_webdriver()
    login(driver, user_id, user_pw)  # 로그인 수행
    # 로그인 후 검색 페이지로 이동하여 크롤링 실행
    auction_data = run_crawling(driver, input_data, building_codes)
    print("=== 크롤링 완료 ===\n")
    print(auction_data)
