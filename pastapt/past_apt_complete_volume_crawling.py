#  아실->입주물량 접속
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import re
import time
import pandas as pd

from pastapt.past_apt_complete_volume_db_utils import drop_apt_complete_volume_table, create_apt_complete_volume_table, \
    insert_apt_complete_volume_record

# 1. 지역 코드 매핑
region_map = {
    "11": "서울특별시", "41": "경기도", "26": "부산특별시", "27": "대구광역시", "28": "인천광역시",
    "29": "광주광역시", "30": "대전광역시", "31": "울산광역시", "36": "세종특별자치시", "42": "강원특별자치도",
    "43": "충청북도", "44": "충청남도", "45": "전라북도", "46": "전라남도", "47": "경상북도",
    "48": "경상남도", "50": "제주특별자치도"
}

# 3. 지역별 파싱 함수
def parse_area(driver, region_code, region_name):
    url = f"https://asil.kr/app/household_rts_list.jsp?os=pc&area={region_code}"
    driver.get(url)
    time.sleep(3)  # JS 렌더링 대기

    soup = BeautifulSoup(driver.page_source, "html.parser")
    rows = soup.select("table#tableList tbody tr")
    parsed = []

    for row in rows:
        cols = row.select("td")
        if len(cols) != 4:
            continue

        address = cols[0].get_text(strip=True)
        apt_name = cols[1].get_text(strip=True)
        year_month = cols[2].get_text(strip=True).replace("년 ", "-").replace("월", "")
        vol_text = cols[3].get_text(strip=True)

        vol_match = re.search(r"[\d,]+", vol_text)
        volume = int(vol_match.group().replace(",", "")) if vol_match else 0

        parsed.append({
            "region": region_name,
            "address": address,
            "apt_name": apt_name,
            "year_month": year_month,
            "volume": volume
        })

    print(f"✔ {region_name} 완료 ({len(parsed)}건)")
    return parsed

# 2. 크롬 드라이버 설정 함수
def create_driver():
    options = Options()
    options.add_argument("--headless")  # 브라우저 창 없이 실행
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)

# 4. 메인 함수
def main():
    driver = create_driver()
    result_data = []

    print("🏗️ 아파트 입주 물량 데이터 수집 시작...")
    for code, name in region_map.items():
        data = parse_area(driver, code, name)
        result_data.extend(data)

    driver.quit()

    # 결과 출력
    print(f"\n📊 총 수집 건수: {len(result_data)}건\n")

    # 분양물량 테이블 생성 및 테이블 삭제
    drop_apt_complete_volume_table()  # 기존 테이블 삭제
    create_apt_complete_volume_table()

    # DataFrame으로 보기 좋게 출력
    df = pd.DataFrame(result_data)
    print(df.head(20))  # 상위 20개 미리보기
    # 파일로 저장
    #df.to_csv("아파트입주물량.txt", sep="\t", index=False)

    # year_month를 YYYY-MM 형식으로 변환 후 테이블에 insert
    for row in result_data:
        ym = row["year_month"]
        # 이미 YYYY-MM 형식이면 그대로, 아니면 변환
        if not re.match(r"\d{4}-\d{2}", ym):
            ym = re.sub(r"(\d{4})-(\d{1,2})", lambda m: f"{m.group(1)}-{int(m.group(2)):02d}", ym)
        # insert 함수 호출 (함수는 별도 구현 필요)
        insert_apt_complete_volume_record(
            row["region"],
            row["address"],
            row["apt_name"],
            ym,
            row["volume"]
        )

# 5. 실행
if __name__ == "__main__":
    main()
