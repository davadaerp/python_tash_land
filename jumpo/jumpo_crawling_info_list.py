import re
import time

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
#
from jumpo.jumpo_db_utils import jumpo_read_db, jumpo_save_info_list_to_sqlite, jumpo_select_info_list_single

# 글로벌 변수 설정
page_list = "60"
data_list = []
saved_count = 0    # 누적 저장 건수

# 저장 방식 선택: "csv" 또는 "sqlite"
SAVE_MODE = "sqlite"  # 원하는 방식으로 변경 가능 (예: "csv")
BATCH_SIZE = 120     # 레코드 1000건마다 저장

# 주소로 시군구 데이타 파싱및 분석
def extract_info(driver, item_id, item_no, section):

    try:
        # 1) 상세 페이지 열기
        driver.get(f"https://www.jumpoline.com/_jumpo/jumpo_view.asp?webjofrsid={item_id}")

        # 2) 테이블 로드 대기
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.detailText_wrap table table tbody tr")
            )
        )

        # 3) 모든 tr 요소 가져오기
        rows = driver.find_elements(
            By.CSS_SELECTOR,
            "div.detailText_wrap table table tbody tr"
        )

        fields = {}
        # 4) 각 tr에서 th/td 쌍 처리
        for tr in rows:
            ths = tr.find_elements(By.TAG_NAME, "th")
            tds = tr.find_elements(By.TAG_NAME, "td")
            for th, td in zip(ths, tds):
                key = th.text.strip()

                # td 안의 중첩 태그 텍스트 우선 수집
                parts = []
                for tag in ("span", "strong", "em"):
                    for el in td.find_elements(By.TAG_NAME, tag):
                        txt = el.text.strip()
                        if txt:
                            parts.append(txt)
                    # 하나라도 모았으면 더 이상 다른 태그는 보지 않고 탈출
                    if parts:
                        break

                # nested-tag에서 아무것도 못 모았으면, td 전체 텍스트로 대체
                if not parts:
                    # 전체 텍스트 보충 (중복 방지)
                    full = td.text.strip()
                    if full and full not in parts:
                        parts.append(full)

                fields[key] = " ".join(parts)

        # 5) 개별 변수로 뽑아내기
        업종           = fields.get("업종")
        도로명_주소    = fields.get("도로명 주소")
        지번_주소      = fields.get("지번 주소")
        건축물종류     = fields.get("건축물 종류")
        해당층수       = fields.get("해당층수")
        대지면적       = fields.get("대지면적")
        전용면적       = fields.get("전용면적")
        공급면적       = fields.get("공급면적")
        건축물주용도   = fields.get("건축물 주용도")
        건축물총층수   = fields.get("건축물 총층수")
        총주차대수     = fields.get("총 주차대수")
        사용승인일     = fields.get("사용승인일")
        권리금         = fields.get("권리금")
        가맹비용       = fields.get("가맹비용")
        보증금         = fields.get("보증금")
        월세          = fields.get("월 세")
        관리비        = fields.get("관리비")
        창업비용       = fields.get("창업비용")
        월매출         = fields.get("월매출")
        입점비용       = fields.get("입점비용")
        마진율         = fields.get("마진율")
        월인건비       = fields.get("월인건비")
        매출이익       = fields.get("매출이익")
        공과비용       = fields.get("공과비용")
        경비합계       = fields.get("경비합계")
        기타비용       = fields.get("기타비용")
        월수익         = fields.get("월수익")
        월수익률       = fields.get("월수익률")
        손익분기점     = fields.get("손익분기점")
        권리금_회수기간 = fields.get("권리금 회수기간")

        def zero_if_none(val):
            return val if val else "0"

        # 6) entry 조합 및 출력
        record = {
            "id":               item_id,
            "item_no":          item_no,
            "section":          section,
            "업종":             업종,
            "도로명주소":      도로명_주소,
            "지번주소":        지번_주소,
            "건축물종류":       건축물종류,
            "해당층수":         해당층수,
            "대지면적":         대지면적,
            "전용면적":         전용면적,
            "공급면적":         공급면적,
            "건축물주용도":     건축물주용도,
            "건축물총층수":     건축물총층수,
            "총주차대수":       총주차대수,
            "사용승인일":       사용승인일,
            "권리금":           zero_if_none(권리금),
            "가맹비용":         zero_if_none(가맹비용),
            "보증금":           zero_if_none(보증금),
            "월세":            zero_if_none(월세),
            "관리비":          zero_if_none(관리비),
            "창업비용":         zero_if_none(창업비용),
            "월매출":           zero_if_none(월매출),
            "입점비용":         zero_if_none(입점비용),
            "마진율":           zero_if_none(마진율),
            "월인건비":         zero_if_none(월인건비),
            "매출이익":         zero_if_none(매출이익),
            "공과비용":         zero_if_none(공과비용),
            "경비합계":         zero_if_none(경비합계),
            "기타비용":         zero_if_none(기타비용),
            "월수익":           zero_if_none(월수익),
            "월수익률":         월수익률,
            "손익분기점":       손익분기점,
            "권리금회수기간":  권리금_회수기간,
        }
        data_list.append(record)

        print(f"[{record}")

    except Exception as e:
        print("데이터 처리 오류:", e)
    # finally:
    #     driver.quit()

def process_records(driver):
    """
    DB에서 레코드 읽어와 extract_info 처리 및 배치 저장
    """
    global saved_count, data_list
    # 전체 메뉴목록DB 레코드 조회
    records = jumpo_read_db()
    for record in records:
        item_id = record['id']
        item_no = record['item_no']
        section = record['section']

        # 이미 상세정보가 저장되어 있으면 스킵
        if jumpo_select_info_list_single(item_no) is not None:
            print(f"Info 레코드 {item_no} 이미 존재, 삽입 스킵.")
            continue

        # 상세현황 파싱 처리
        extract_info(driver, item_id, item_no, section)

        # 배치 사이즈 도달 시 저장
        if len(data_list) >= BATCH_SIZE:
            print(f"저장 전 누적: {saved_count + len(data_list)}건, 배치: {len(data_list)}건")
            jumpo_save_info_list_to_sqlite(data_list)
            saved_count += len(data_list)
            data_list.clear()
            time.sleep(1)

def main():
    global saved_count, data_list
    # 1) Selenium 으로 메뉴 목록 추출
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)
    #driver = webdriver.Chrome()
    try:
        process_records(driver)
        # 남은 데이터 저장
        if data_list:
            print(f"최종 저장: {len(data_list)}건")
            jumpo_save_info_list_to_sqlite(data_list)
            saved_count += len(data_list)

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
