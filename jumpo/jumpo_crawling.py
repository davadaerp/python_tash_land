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
from jumpo.jumpo_db_utils import jumpo_save_to_sqlite, jumpo_drop_table

# 글로벌 변수 설정
page_list = "60"
data_list = []
saved_count = 0    # 누적 저장 건수

# 저장 방식 선택: "csv" 또는 "sqlite"
SAVE_MODE = "sqlite"  # 원하는 방식으로 변경 가능 (예: "csv")
BATCH_SIZE = 120     # 레코드 1000건마다 저장

# —————————————————————————————————————————————————————————
# 1) 전역 detail_driver 선언
detail_driver = None
# —————————————————————————————————————————————————————————

def menu_list(html):
    """
    HTML 문자열에서 '전체업종' 메뉴를 찾아
    각 카테고리(section, name, mcode, scode, page, total)를 추출합니다.
    """
    soup = BeautifulSoup(html, 'html.parser')

    # 1. 전체업종 메뉴를 id로 찾기
    menu8 = soup.find('li', id='Z_return_change_div')
    if not menu8:
        raise RuntimeError("[menu_list] '전체업종' li#Z_return_change_div 요소를 찾을 수 없습니다.")

    # 2. 서브 메뉴 컨테이너는 class='menu_all'
    menu_all = menu8.find('div', class_=lambda x: x and 'menu_all' in x)
    if not menu_all:
        raise RuntimeError("[menu_list] 'div.menu_all' 요소를 찾을 수 없습니다.")

    results = []
    # 3. 각 카테고리 ul.all_menu 순회
    for ul in menu_all.select('ul.all_menu'):
        title_li = ul.find('li', class_='title')
        if not title_li:
            continue
        section_title = title_li.get_text(strip=True)

        for item in ul.find_all('li', class_='item_text'):
            a = item.find('a', onclick=True)
            if not a:
                continue
            onclick = a['onclick']
            m = re.search(
                r"CateChgSelect\(\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*'([^']*)'\s*\)",
                onclick
            )
            if not m:
                continue
            mcode, scode, name, page = m.groups()

            # ——— 여기부터 총건수 추출 로직 ———
            total = None
            # 1) <span class="num">(1234)</span> 형태
            span_num = item.find('span', class_='num')
            if span_num:
                # "(2727)" -> "2727"
                total = re.sub(r'\D', '', span_num.get_text())
            else:
                # 2) <p class="menu_num"><span>2727</span></p> 형태
                p_num = item.find('p', class_='menu_num')
                if p_num:
                    total = re.sub(r'\D', '', p_num.get_text())

            results.append({
                'section': section_title,
                'name': name,
                'mcode': mcode,
                'scode': scode,
                'page': page,
                'total': int(total) if total else None
            })

    return results

# ======================================================================
# 레코드 데이터 처리
# 결과가 로드될 때까지 대기 (#marketListTable 안의 ul.jplist li 요소들이 로드될 때까지)
# ======================================================================
def record_parsing_list(driver, section, current_page):
    global saved_count, data_list

    # 1) li 요소가 로드될 때까지 대기
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "#marketListTable ul.jplist li")
        )
    )
    #
    items = driver.find_elements(
        By.CSS_SELECTOR,
        "#marketListTable ul.jplist li .s_left"
    )
    for idx, li in enumerate(items, start=1):
        text_div = li.find_element(By.CSS_SELECTOR, "div.text")

        # (A) 광고 고유 ID 추출: 먼저 span.nocode에서
        no_code = text_div.find_element(By.CSS_SELECTOR, "span.nocode")
        onclick_js = no_code.get_attribute("onclick")
        m = re.search(r"f_itemwin\('jumpo','(\d+)'", onclick_js or "")
        item_id = m.group(1) if m else None

        # span.nocode에 ID가 없으면, h4 태그의 onclick에서도 시도
        if not item_id:
            try:
                h4 = text_div.find_element(By.TAG_NAME, "h4")
                onclick_js2 = h4.get_attribute("onclick")
                m2 = re.search(r"f_itemwin\('jumpo','(\d+)'", onclick_js2 or "")
                item_id = m2.group(1) if m2 else None
            except Exception:
                item_id = None

        # (B) 매물번호
        try:
            item_no = no_code.find_element(By.TAG_NAME, "strong").text.strip()
        except:
            item_no = None

        # (C) 지역·업종
        loc_cate = text_div.find_element(By.CSS_SELECTOR, "span.cate").text.strip()
        upjong = text_div.find_element(By.CSS_SELECTOR, "strong.t_mcate").text.strip()
        region = loc_cate.replace(upjong, "")
        # 예: "서울시 마포구 도화동카페" → 지역/업종 분리 필요 시 추가 파싱
        #
        # # (D) 프랜차이즈명
        # #franch_name = text_div.find_element(By.CSS_SELECTOR, "span.franch_name").text.strip()
        #
        # # (E) 층·면적
        # floor = text_div.find_element(By.CSS_SELECTOR, "strong.space").text.strip()
        # area = text_div.find_element(By.CSS_SELECTOR, "span.floor").text.strip()
        #
        # # (F) 실매물 확인일·조회수
        # date = text_div.find_element(By.CSS_SELECTOR, "span.date em").text.strip()
        # hits = text_div.find_element(By.CSS_SELECTOR, "span.hits em").text.strip()
        #
        # # (G) 제목·부제·설명
        # title = text_div.find_element(By.TAG_NAME, "h4").text.strip()
        # subtitle = text_div.find_element(By.CSS_SELECTOR, "p.bxsubtit").text.strip()
        # desc = text_div.find_element(By.CSS_SELECTOR, "p.copy").text.strip()
        #
        # # (H) 가격 정보
        # price_p = text_div.find_element(By.CSS_SELECTOR, "p.price")
        # premium = price_p.find_element(By.CSS_SELECTOR, "span.premium strong").text.strip()
        # # franch_cost = price_p.find_element(By.CSS_SELECTOR, "span.franchmem_cost strong").text.strip() or None
        # monthly_income = price_p.find_elements(By.CSS_SELECTOR, "span.teright strong")[0].text.strip()
        # monthly_rate = price_p.find_elements(By.CSS_SELECTOR, "span.teright b")[0].text.strip() + '%'
        #
        # # (I) 보증금·월세·창업비용
        # deposit = price_p.find_element(By.CSS_SELECTOR, "span.priceri_area span:nth-child(1) strong").text.strip()
        # #monthly_rent = price_p.find_element(By.CSS_SELECTOR, "span.mthfee strong").text.strip()
        # startup_cost = price_p.find_element(By.CSS_SELECTOR, "span.total strong").text.strip()
        #
        # # (J) 중개사 정보
        # # #agent_elem = text_div.find_element(By.CSS_SELECTOR, "p.regist4rule span.agent span.name")
        # # agent_name = agent_elem.text.replace(agent_elem.find_element(By.TAG_NAME, "strong").text, "").strip()
        # # agent_phone = agent_elem.find_element(By.TAG_NAME, "strong").text.strip()
        #
        # 딕셔너리에 담아 저장
        record = {
            "section": section,
            "id": item_id,
            "item_no": item_no,     # 매물번호
            "region": region,       # 지역
            "upjong": upjong,       # 업종
            # #"프랜차이즈명": franch_name,
            # "층": floor,
            # "면적": area,
            # "확인일": date,
            # "조회수": hits,
            # "제목": title,
            # "부제": subtitle,
            # "설명": desc,
            # "권리금": premium,
            # # "가맹비용": franch_cost,
            # "월수익": monthly_income,
            # "수익률": monthly_rate,
            # "보증금": deposit,
            # #"월세": monthly_rent,
            # "창업비용": startup_cost,
            # # "중개사명": agent_name,
            # # "중개사연락처": agent_phone,
            "page": current_page
        }
        data_list.append(record)

        # 1000건마다 저장 처리
        if len(data_list) >= BATCH_SIZE:
            print(f"저장 전 현재까지 저장 건수: {saved_count + len(data_list)} 건, 이번 배치: {len(data_list)} 건")
            jumpo_save_to_sqlite(data_list)
            saved_count += len(data_list)
            data_list.clear()
            time.sleep(1)

        print(f"[{idx}] {record}")

        # 상세현황 파싱처리
        #extract_info(item_id, item_no, section)
        #time.sleep(1)

    # 누적 파싱 개수
    total = (current_page - 1) * len(items) + idx
    print(f"📄 현재 페이지: {current_page}, 페이지 내 항목 수: {idx}, 누적 읽기: {total}")


# 페이징 이동 및 데이터 처리
def navigate_pages(driver, section, total_records):
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
            # → 문자열 인자로 전달하고, 괄호를 올바르게 닫습니다.
            if page_no > 1:
                driver.execute_script(f"Worker.draw_mid_data('{page_no}');")
                time.sleep(5)  # 페이지 로딩 대기

            # 레코드 파싱 및 데이터 저장
            record_parsing_list(driver, section, page_no)

        except Exception as e:
            print("❌ 페이지 이동 중 오류 발생 또는 마지막 페이지 도달:", e)
            break



# 주소로 시군구 데이타 파싱및 분석
def extract_info(item_id, item_no, section):
    global detail_driver

    try:
        # 1) 상세 페이지 열기
        detail_driver.get(f"https://www.jumpoline.com/_jumpo/jumpo_view.asp?webjofrsid={item_id}")

        # 2) 테이블 로드 대기
        WebDriverWait(detail_driver, 20).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.detailText_wrap table table tbody tr")
            )
        )

        # 3) 모든 tr 요소 가져오기
        rows = detail_driver.find_elements(
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
        entry = {
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
        print(entry)

    except Exception as e:
        print("데이터 처리 오류:", e)
    # finally:
    #     driver.quit()

def main():
    global detail_driver

    # 1) Selenium 으로 메뉴 목록 추출
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    #driver = webdriver.Chrome(options=chrome_options)
    driver = webdriver.Chrome()

    detail_driver = webdriver.Chrome(options=chrome_options)
    try:
        # 원하는 mcode/scode 로 리스트 페이지 열기 (전체업종 버튼이 있으면 어느 페이지든 OK)
        driver.get("https://www.jumpoline.com/_jumpo/jumpoListMaster.asp?mcode=B&scode=14")
        time.sleep(3)

        first_html = driver.page_source
        categories = menu_list(first_html)
        print(f"총 {len(categories)}개 카테고리 발견\n")
        for cat in categories:
            print(f"▶ [{cat['section']}] {cat['name']} total: {cat['total']}건, mcode={cat['mcode']}, scode={cat['scode']}")

        # 맨처음 목록리스트 전부를 삭제후 처리함
        #jumpo_drop_table()

        # 3) 각 카테고리에 대해 1~3페이지만 예시로 읽어보기
        for cat in categories:
            print(
                f"▶ [{cat['section']}] {cat['name']} total: {cat['total']}건, mcode={cat['mcode']}, scode={cat['scode']} 데이터 가져오는 중...")
            #
            section = cat['section']    # 휴계음식점
            mcode = cat['mcode']
            scode = cat['scode']
            total_records = cat['total']
            #
            driver.get("https://www.jumpoline.com/_jumpo/jumpoListMaster.asp?mcode=" + mcode +"&scode=" + scode)
            time.sleep(1)
            navigate_pages(driver, section, total_records)

    finally:
        driver.quit()
        detail_driver.quit()

if __name__ == "__main__":
    main()
