# 과거매매지수 가져오기(년단위,6개월,3개월,월단위,주단위 선택하여 가져오기 가능)
#
# 현재기준 매매및 전세시세 가져오기 => 이 부문은 과거매매지수 가져온데이타 기준으로 past_apt에 매매(하/상안가)및 전세(하/상안가)를 세팅한다.(현재월)
# 현재월 update하면서 past_apt_price에 해당월 insert하여 pir조회에 사용한다.
#
import os

# 부동산뱅크 접속id(wfight66/몽셍이69)
# const
# regions = [
#     {name: "서울특별시", url: "https://www.neonet.co.kr/novo-rebank/view/agency_zone/AgencyZoneIndex.neo?lcode=01"},
#     {name: "경기도", url: "https://www.neonet.co.kr/novo-rebank/view/agency_zone/AgencyZoneIndex.neo?lcode=02"},
#     {name: "부산광역시", url: "https://www.neonet.co.kr/novo-rebank/view/agency_zone/AgencyZoneIndex.neo?lcode=03"},
#     {name: "대구광역시", url: "https://www.neonet.co.kr/novo-rebank/view/agency_zone/AgencyZoneIndex.neo?lcode=04"},
#     {name: "인천광역시", url: "https://www.neonet.co.kr/novo-rebank/view/agency_zone/AgencyZoneIndex.neo?lcode=05"},
#     {name: "광주광역시", url: "https://www.neonet.co.kr/novo-rebank/view/agency_zone/AgencyZoneIndex.neo?lcode=06"},
#     {name: "대전광역시", url: "https://www.neonet.co.kr/novo-rebank/view/agency_zone/AgencyZoneIndex.neo?lcode=07"},
#     {name: "강원도", url: "https://www.neonet.co.kr/novo-rebank/view/agency_zone/AgencyZoneIndex.neo?lcode=08"},
#     {name: "경상남도", url: "https://www.neonet.co.kr/novo-rebank/view/agency_zone/AgencyZoneIndex.neo?lcode=10"},
#     {name: "경상북도", url: "https://www.neonet.co.kr/novo-rebank/view/agency_zone/AgencyZoneIndex.neo?lcode=11"},
#     {name: "전라남도", url: "https://www.neonet.co.kr/novo-rebank/view/agency_zone/AgencyZoneIndex.neo?lcode=12"},
#     {name: "전라북도", url: "https://www.neonet.co.kr/novo-rebank/view/agency_zone/AgencyZoneIndex.neo?lcode=13"},
#     {name: "제주특별자치도", url: "https://www.neonet.co.kr/novo-rebank/view/agency_zone/AgencyZoneIndex.neo?lcode=14"},
#     {name: "충청남도", url: "https://www.neonet.co.kr/novo-rebank/view/agency_zone/AgencyZoneIndex.neo?lcode=15"},
#     {name: "충청북도", url: "https://www.neonet.co.kr/novo-rebank/view/agency_zone/AgencyZoneIndex.neo?lcode=16"},
#     {name: "울산광역시", url: "https://www.neonet.co.kr/novo-rebank/view/agency_zone/AgencyZoneIndex.neo?lcode=17"},
#     {name: "세종특별자치시", url: "https://www.neonet.co.kr/novo-rebank/view/agency_zone/AgencyZoneIndex.neo?lcode=19"},
# ];
# 서울/강남구/개포동 => lcode:지역, mcode: 시군구, sname: 동/읍
# https://www.neonet.co.kr/novo-rebank/view/market_price/PastMarketPriceList.neo?lcode=01&mcode=135&sname=개포동

# 시군구코드 가져오기
# https://www.neonet.co.kr/novo-rebank/view/market_price/RegionData.neo?offerings_gbn=AT&lcode=01&mcode=&target=mcode&update=140228
# # 강남구(135)에 읍명동명 가져오기
# https://www.neonet.co.kr/novo-rebank/view/market_price/RegionData.neo?offerings_gbn=AT&lcode=01&mcode=135&target=sname&update=140228
# # 상세현황목록 - 논현동
# https://www.neonet.co.kr/novo-rebank/view/market_price/PastMarketPriceList.neo?lcode=01&mcode=135&sname=%B3%ED%C7%F6%B5%BF
#
# if (document.getElementById('sname') && document.getElementById('sname').value) {
#     param += '&sname=' + encodeURIComponent(document.getElementById('sname').value);
# }
# https://www.neonet.co.kr/novo-rebank/view/market_price/PastMarketPriceList.neo?lcode=01&mcode=135&sname=encodeURIComponent('삼성동')
# 연간자료 출력 상세현황(제주도=>제주시=>화북동=>화북주공4단지
# https://www.neonet.co.kr/novo-rebank/view/market_price/PastMarketPriceDetail.neo?lcode=14&mcode=690&sname=%C8%AD%BA%CF%B5%BF&complex_cd=A1012009&pyung_cd=1
#
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
import csv
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from urllib.parse import quote

from pastapt.past_apt_db_utils import past_apt_create_table, insert_apt_and_prices

# 폼로그인처리
def login(driver):
    try:
        # 아이디 입력 필드 로딩 대기
        username_field = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.NAME, "id"))
        )
        password_field = driver.find_element(By.NAME, "pw")

        # 로그인 정보 입력
        username_field.clear()
        username_field.send_keys("wfight69")
        password_field.send_keys("ahdtpddl0")

        # 로그인 버튼 클릭
        submit_button = driver.find_element(By.XPATH, "//input[@type='image' and contains(@src, 'btn_login01.gif')]")
        submit_button.click()

        print("로그인 시도 완료.")
    except Exception as e:
        print("로그인 오류:", e)

# 지역 정보 리스트
regions = [
    {"name": "서울특별시", "lcode": "01"},
    {"name": "경기도", "lcode": "02"},
    {"name": "부산광역시", "lcode": "03"},
    {"name": "대구광역시", "lcode": "04"},
    {"name": "인천광역시", "lcode": "05"},
    {"name": "광주광역시", "lcode": "06"},
    {"name": "대전광역시", "lcode": "07"},
    {"name": "강원도", "lcode": "08"},
    {"name": "경상남도", "lcode": "10"},
    {"name": "경상북도", "lcode": "11"},
    {"name": "전라남도", "lcode": "12"},
    {"name": "전라북도", "lcode": "13"},
    {"name": "제주특별자치도", "lcode": "14"},
    {"name": "충청남도", "lcode": "15"},
    {"name": "충청북도", "lcode": "16"},
    {"name": "울산광역시", "lcode": "17"},
    {"name": "세종특별자치시", "lcode": "19"}
]

# 시군구가져오기 코드
def get_mcode_list(lcode):
    url = f"https://www.neonet.co.kr/novo-rebank/view/market_price/RegionData.neo?offerings_gbn=AT&lcode={lcode}&mcode=&target=mcode&update=140228"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    try:
        response = requests.get(url, headers=headers)
        response.encoding = "euc-kr"  # 응답 인코딩 설정
        if response.status_code != 200:
            print(f"요청 실패: 상태 코드 {response.status_code}")
            return []

        root = ET.fromstring(response.text)
        mcode_list = []

        for node in root.findall(".//n"):
            mcode = node.find("code").text.strip()
            name = node.find("name").text.strip()
            mcode_list.append({"mcode": mcode, "name": name})

        return mcode_list

    except Exception as e:
        print("시군구 가져오기 실패:", e)
        return []

# 위 시.군.구코드(mcode)를 자기고서 읍.면.동을 가져오기
def get_sname_list(lcode, mcode):
    url = f"https://www.neonet.co.kr/novo-rebank/view/market_price/RegionData.neo?offerings_gbn=AT&lcode={lcode}&mcode={mcode}&target=sname&update=140228"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    try:
        response = requests.get(url, headers=headers)
        response.encoding = "euc-kr"
        if response.status_code != 200:
            print(f"요청 실패: 상태 코드 {response.status_code}")
            return []

        root = ET.fromstring(response.text)
        sname_list = []

        for node in root.findall(".//n"):
            code = node.find("code").text.strip()
            name = node.find("name").text.strip()
            sname_list.append({"sname_code": code, "sname": name})

        return sname_list

    except Exception as e:
        print("읍면동 가져오기 실패:", e)
        return []


# 시군구=>읍면동=>아파트목록
def get_past_market_list(lcode, mcode, sname):
    encoded_sname = quote(sname, encoding="euc-kr")
    url = f"https://www.neonet.co.kr/novo-rebank/view/market_price/PastMarketPriceList.neo?lcode={lcode}&mcode={mcode}&sname={encoded_sname}"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    try:
        response = requests.get(url, headers=headers)
        response.encoding = "euc-kr"

        if response.status_code != 200:
            print(f"[요청 실패] 상태코드: {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        container = soup.find("div", id="divMarketPriceList")
        if not container:
            print("시세 테이블 div를 찾을 수 없습니다.")
            return None

        rows = container.find_all("tr")
        result = []
        current_apt_name = None
        current_apt_link = None

        for row in rows:
            tds = row.find_all("td")
            if not tds:
                continue

            # 아파트명 있는 행 (rowspan 있는 첫 줄)
            if tds[0].has_attr("rowspan"):
                current_apt_name = tds[0].get_text(strip=True)
                link_tag = tds[0].find("a")
                current_apt_link = link_tag["href"] if link_tag else None

                size = tds[1].get_text(strip=True)
                detail_link = tds[1].find("a")["href"] if tds[1].find("a") else None
                prices = [td.get_text(strip=True) for td in tds[2:]]

            # 두 번째 줄 (아파트명 생략된 줄)
            else:
                size = tds[0].get_text(strip=True)
                detail_link = tds[0].find("a")["href"] if tds[0].find("a") else None
                prices = [td.get_text(strip=True) for td in tds[1:]]

            result.append({
                "apartment": current_apt_name,
                "size": size,
                "price_history": prices,
                "apt_link": current_apt_link,
                "detail_link": detail_link
            })

        return result

    except Exception as e:
        print(f"[에러] {e}")
        return None

# 상세년도별 데이타 파싱처리 = 동작안함
def parse_detail_market_price(detail_url):
    full_url = f"{detail_url}"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    try:
        response = requests.get(full_url, headers=headers)
        response.encoding = "euc-kr"

        if response.status_code != 200:
            print(f"[요청 실패] 상태 코드: {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        container = soup.find("div", id="divMarketPriceList")
        if not container:
            print("상세 시세 테이블을 찾을 수 없습니다.")
            return None

        table = container.find("table")
        rows = table.find_all("tr")[2:]  # 헤더 두 줄 제외

        detail_data = []

        for row in rows:
            cols = [td.get_text(strip=True) for td in row.find_all("td")]
            if len(cols) == 7:
                detail_data.append({
                    "month": cols[0],
                    "sale_low": cols[1],
                    "sale_high": cols[2],
                    "sale_change": cols[3],
                    "rent_low": cols[4],
                    "rent_high": cols[5],
                    "rent_change": cols[6]
                })

        return detail_data

    except Exception as e:
        print(f"[상세 페이지 파싱 오류] {e}")
        return None

def parse_value(val):
    return 0 if val in ["-", "--"] else val
#
def parse_detail_market_price_selenium(driver):

    try:
        # 1. 특정 ID 요소가 실제 '화면'에 보일 때까지 대기
        WebDriverWait(driver, 1).until(
            EC.presence_of_element_located((By.ID, "divMarketPriceList"))
        )
        # 2. 아주 짧은 추가 대기 (JS 렌더링 완성을 위함)
        time.sleep(0.3)  # 약간의 안정성 대기

        # 3. BeautifulSoup으로 파싱 시점의 소스 캡처
        html_source = driver.page_source
        soup = BeautifulSoup(html_source, "html.parser")

        # 상세 시세 정보 파싱
        detail_data = []
        container = soup.find("div", id="divMarketPriceList")
        if not container:
            print("상세 시세 테이블을 찾을 수 없습니다.")
        else:
            table = container.find("table")
            rows = table.find_all("tr")[2:]  # 헤더 두 줄 제외

            for row in rows:
                cols = [td.get_text(strip=True) for td in row.find_all("td")]
                if len(cols) == 7:
                    detail_data.append({
                        "month": cols[0],
                        "sale_low": parse_value(cols[1]),
                        "sale_high": parse_value(cols[2]),
                        "sale_change": cols[3],
                        "rent_low": parse_value(cols[4]),
                        "rent_high": parse_value(cols[5]),
                        "rent_change": cols[6]
                    })

        # 단지 프로필 정보 파싱
        profile = {}
        profile_container = soup.find("div", class_="reg_list_all")
        if profile_container:
            inner_table = profile_container.find("table")
            if inner_table:
                rows = inner_table.find_all("tr")
                for row in rows:
                    cols = row.find_all("td")
                    for col in cols:
                        text = col.get_text(strip=True)
                        if "총 가구수" in text:
                            profile['total_households'] = text.split(":")[-1].strip()
                        elif "입주년도" in text:
                            profile['move_in_date'] = text.split(":")[-1].strip()
                        elif "건설사" in text:
                            profile['builder'] = text.split(":")[-1].strip()
                        elif "동수/층수" in text:
                            profile['building_floors'] = text.split(":")[-1].strip()
                        elif "주차대수" in text:
                            profile['parking'] = text.split(":")[-1].strip()
                        elif "난방방식" in text:
                            profile['heating_type'] = text.split(":")[-1].strip()
        else:
            print("단지 프로필 정보를 찾을 수 없습니다.")

        return {
            "profile": profile,
            "market_prices": detail_data
        }

    except Exception as e:
        # 에러 발생 시 현재 URL과 에러 메시지 출력
        print(f"❌ [페이지 파싱 오류] URL: {driver.current_url}")
        print(f"에러 내용: {str(e)}")
        return None


# 반복 분석용 함수 예시
def analyze_from_json(driver):
    try:
        # database & table 생성
        past_apt_create_table()

        print("📂 지역 계층구조 JSON 파일에서 분석 시작...")

        filename = "region_hierarchy.json"
        with open(filename, encoding="utf-8-sig") as f:
            hierarchy = json.load(f)

        # JSON 계층구조 순회: 대분류(지역) → 중분류(시군구) → 소분류(읍면동)
        for region in hierarchy:
            region_name = region["region_name"]
            lcode = region["lcode"]
            for mcode_obj in region.get("하위", []):
                mcode = mcode_obj["mcode"]
                mcode_name = mcode_obj["mcode_name"]
                for s_obj in mcode_obj.get("하위", []):
                    sname = s_obj["sname"]
                    print(f"\n[ {region_name} > {mcode_name} > {sname} ]")
                    data = get_past_market_list(lcode, mcode, sname)
                    if data:
                        for row in data:
                            time.sleep(0.1)  # 약간의 안정성 대기
                            apt_name = row["apartment"]
                            size = re.sub(r'[^0-9.]', '', row["size"])
                            print(f"{apt_name} | {size}㎡ | 가격: {row['price_history']}")
                            print(f"상세 링크: {row['detail_link']}")
                            print()
                            if row['detail_link']:
                                detail_url = row['detail_link']
                                driver.get(detail_url)  # driver는 여기서 한 번만 이동
                                # detail = parse_detail_market_price(detail_url)
                                detail = parse_detail_market_price_selenium(driver)
                                if detail:
                                    profile = detail.get("profile", {})
                                    market_prices = detail.get("market_prices", [])
                                    print(f"📌 단지 프로필 정보({apt_name})")
                                    print(f" - 평형(공급)       : {size}m2")
                                    print(f" - 총 가구수        : {profile.get('total_households', '정보 없음')}")
                                    print(f" - 입주년도         : {profile.get('move_in_date', '정보 없음')}")
                                    print(f" - 건설사          : {profile.get('builder', '정보 없음')}")
                                    print(f" - 동수/층수        : {profile.get('building_floors', '정보 없음')}")
                                    print(f" - 주차대수         : {profile.get('parking', '정보 없음')}")
                                    print(f" - 난방방식         : {profile.get('heating_type', '정보 없음')}")
                                    print("============================")
                                    print("\n📊 월별 시세 정보")
                                    for d in market_prices:
                                        print(
                                            f" - {d['month']} | 매매 {d['sale_low']}~{d['sale_high']} ({d['sale_change']}), 전세 {d['rent_low']}~{d['rent_high']} ({d['rent_change']})"
                                        )
                                    print("\n")
                                    #
                                    insert_apt_and_prices(apt_name, detail, region_name, mcode_name, sname, size)

    except FileNotFoundError:
        print(f"⚠️ 파일을 찾을 수 없습니다: {filename}")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")


# 지역코드 => 시군구명 => 읍면동명을 저장함.
def save_region_hierarchy_to_json(filename="region_hierarchy.json"):
    # 파일이 이미 존재하면 패스
    if os.path.exists(filename):
        print(f"✅ 파일 이미 존재: {filename} → 생성을 건너뜁니다.")
        return

    hierarchy = []  # 최종 JSON 데이터를 담을 리스트

    # 지역별로 lcode, mcode, sname을 가져와서 계층 구조 생성
    # 차후 아래 구조안에 법정동 코드를 추가하여 적용바람
    # "mcode": "135",
    # "mcode_name": "강남구",
    # "stdg_cd": "4311000000",  # 법정동코드(청주시: 4311000000)

    for region in regions:
        region_name = region["name"]
        lcode = region["lcode"]
        # 대분류: 지역 코드
        region_obj = {
            "lcode": lcode,
            "region_name": region_name,
            "하위": []  # 시군구 목록
        }

        mcode_list = get_mcode_list(lcode)
        for m in mcode_list:
            mcode = m["mcode"]
            mcode_name = m["name"]
            # 중분류: 시군구
            mcode_obj = {
                "mcode": mcode,
                "mcode_name": mcode_name,
                "하위": []  # 읍면동 목록
            }

            sname_list = get_sname_list(lcode, mcode)
            for item in sname_list:
                sname = item["sname"]
                sname_code = item["sname_code"]
                # 소분류: 읍면동
                s_obj = {
                    "sname_code": sname_code,
                    "sname": sname
                }
                mcode_obj["하위"].append(s_obj)

            region_obj["하위"].append(mcode_obj)

        hierarchy.append(region_obj)

    # JSON 파일로 저장 (한글이 깨지지 않도록 ensure_ascii=False)
    with open(filename, "w", encoding="utf-8-sig") as f:
        json.dump(hierarchy, f, ensure_ascii=False, indent=2)

    print(f"✅ 저장 완료: {filename}")


def main():
    global json_data, saved_count, data_list  # 전역 변수 사용

    # 크롬드라이버 화면없이 동작하게 처리하는 방법(배치개념에 적용)
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    # chrome_options.add_argument("--disable-gpu")
    # 필요에 따라 추가 옵션 설정: --no-sandbox, --disable-dev-shm-usage 등

    driver = webdriver.Chrome(options=chrome_options)
    #driver = webdriver.Chrome()
    try:
        # 부동산뱅크사이트
        driver.get("https://www.neonet.co.kr/novo-rebank/view/member/MemberLogin.neo")
        driver.implicitly_wait(1)
        #=====
        login(driver)
        time.sleep(2)

        # 지역분석위한 코드 화일을 먼저 저장
        save_region_hierarchy_to_json()

        # 분석시작처리
        analyze_from_json(driver)

    except Exception as e:
        print("오류 발생:", e)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()