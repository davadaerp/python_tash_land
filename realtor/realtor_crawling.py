import os
import time
import json
import datetime
import requests
import re
from bs4 import BeautifulSoup
from realtor_db_utils import realtor_save_to_sqlite
from config import REALTOR_DB_PATH

# 전역 변수 설정
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/90.0.4430.93 Safari/537.36"
    )
}

BATCH_SIZE = 300     # 배치 저장 단위
MAX_PAGE = 3000      # 최대 페이지수
results = []         # 추출된 데이터를 저장할 전역 리스트

# 배치 마지막 정보를 저장할 파일 경로 (JSON 형식)
txt_filename = os.path.join(REALTOR_DB_PATH, "last_mem_no.txt")

# 전역 변수 (현재 시도와 페이지 정보를 저장)
current_sido = None
current_sido_name = None
current_page = 0

def extract_links(url):
    try:
        response = requests.get(url, headers=headers, timeout=10)
    except Exception as e:
        print(f"URL 요청 중 오류 발생: {url} ({e})")
        return []
    if response.status_code != 200:
        print(f"URL 요청 실패: {url} (상태 코드: {response.status_code})")
        return []
    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.find("table", class_="tableList simpleList")
    if not table:
        print("테이블을 찾을 수 없습니다.")
        return []
    tbody = table.find("tbody")
    if not tbody:
        print("tbody를 찾을 수 없습니다.")
        return []
    rows = tbody.find_all("tr")
    links = []
    for row in rows:
        a_tag = row.find("a")
        if a_tag:
            href = a_tag.get("href")
            text = a_tag.get_text(strip=True)
            # moveDetail 함수 호출 문자열에서 숫자만 추출 (예: '1037039')
            mem_no = None
            match = re.search(r"javascript:moveDetail\('(\d+)'", href)
            if match:
                mem_no = match.group(1)
            links.append({"href": href, "text": text, "mem_no": mem_no})
    return links

def extract_and_print_all_links():
    global results, current_sido, current_sido_name, current_page
    sido_options = [
        ("1", "서울특별시"),
        ("2", "경기도"),
        ("3", "인천광역시"),
        ("4", "부산광역시"),
        ("5", "대구광역시"),
        ("6", "광주광역시"),
        ("7", "대전광역시"),
        ("8", "울산광역시"),
        ("9", "강원특별자치도"),
        ("10", "경상남도"),
        ("11", "경상북도"),
        ("12", "전라남도"),
        ("13", "전북특별자치도"),
        ("14", "충청남도"),
        ("15", "충청북도"),
        ("16", "세종특별자치시"),
        ("17", "제주특별자치도")
    ]
    base_url = "https://www.karhanbang.com/office/?topM=09&key=&search=&sel_sido={}&sel_gugun=&sel_dong=&page={}"

    for sido_value, sido_name in sido_options:
        current_sido = sido_value
        current_sido_name = sido_name
        # 이전에 저장된 마지막 페이지를 읽어와서 그 다음 페이지부터 시작
        last_page_saved = get_last_end_info(sido_value)
        start_page = last_page_saved if last_page_saved > 0 else 1
        print(f"==== {sido_name} 시작 (시작 페이지: {start_page}) ====")
        last_processed_page = start_page
        consecutive_empty = 0  # 연속해서 링크가 없는 페이지 수
        for page in range(start_page, MAX_PAGE + 1):
            current_page = page
            url = base_url.format(sido_value, page)
            print(f"페이지 {page}: {url}")
            #
            page_links = extract_links(url)
            if not page_links:
                consecutive_empty += 1
                print(f"{sido_name} 페이지 {page}에서 링크가 없음. (연속 {consecutive_empty}회)")
                # 연속 3회 링크가 없으면 해당 시/도의 처리를 중단
                if consecutive_empty >= 3:
                    last_processed_page = page - consecutive_empty
                    print(f"{sido_name} 연속 {consecutive_empty}회 링크 없음으로 종료.")
                    break
                # 다음 페이지로 이동
                time.sleep(3)
                continue
            else:
                consecutive_empty = 0
            #
            for link in page_links:
                print("Text:", link["text"])
                if link["mem_no"]:
                    mem_no = link["mem_no"]
                    extract_and_parser_link(mem_no)
            print("-" * 40)
            time.sleep(0.3)
        print(f"==== {sido_name} 완료 ====")
        print("=" * 50)
        # 시/도별로 남은 결과 저장
        if results:
            print(f"최종 배치 저장: {len(results)} 건.")
            realtor_save_to_sqlite(results)
            results.clear()
            time.sleep(3)
        # 시/도별 마지막 정보 저장
        save_last_end_info(current_sido, current_sido_name, last_processed_page)

def extract_and_parser_link(mem_no):
    global results, BATCH_SIZE, current_sido, current_sido_name, current_page
    mapping = {
        "제목": "title",
        "대표자": "representative",
        "주소명1": "address1",
        "주소명2": "address2",
        "일반전화": "landline_phone",
        "휴대전화": "mobile_phone"
    }
    url = f"https://www.karhanbang.com/office/office_detail.asp?topM=09&mem_no={mem_no}"
    try:
        response = requests.get(url, headers=headers, timeout=10)
    except Exception as e:
        print(f"mem_no {mem_no}: 요청 중 오류 발생 ({e})")
        return
    if response.status_code != 200:
        print(f"mem_no {mem_no}: 페이지 요청 실패, 상태 코드: {response.status_code}")
        return
    soup = BeautifulSoup(response.text, "html.parser")
    info_div = soup.find("div", class_="realtorsInfoBig clearFix")
    if not info_div:
        print(f"mem_no {mem_no}: 중개사정보 영역을 찾을 수 없습니다.")
        return

    extracted_text = info_div.get_text(separator="\n", strip=True)
    parsed_info = parse_realtor_info(extracted_text)
    parsed_info["mem_no"] = mem_no

    # 한글 키를 영문 키로 치환
    converted_info = {"mem_no": mem_no}
    for kor_key, eng_key in mapping.items():
        converted_info[eng_key] = parsed_info.get(kor_key)

    if is_valid_phone(parsed_info.get("일반전화")) or is_valid_phone(parsed_info.get("휴대전화")):
        converted_info["landline_phone"] = parsed_info.get("일반전화")
        converted_info["mobile_phone"] = parsed_info.get("휴대전화")
        results.append(converted_info)
        print(f"mem_no {mem_no}: 정보 저장 완료. 휴대전화: {converted_info.get('mobile_phone')}, (현재 배치: {len(results)} 건)")
    else:
        print(f"mem_no {mem_no}: 전화번호 없음, 저장 안함.")

    # 배치 저장 조건
    if len(results) >= BATCH_SIZE:
        print(f"저장 전 현재 배치 건수: {len(results)} 건. 저장 수행...")
        realtor_save_to_sqlite(results)
        results.clear()
        # 배치 저장 후 현재 시도, 시도명, 현재 페이지 번호를 업데이트
        save_last_end_info(current_sido, current_sido_name, current_page)
        time.sleep(3)

def parse_realtor_info(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    result = {}
    result["제목"] = lines[0] if lines else ""
    try:
        idx = lines.index("대표자")
        result["대표자"] = lines[idx + 1]
    except ValueError:
        result["대표자"] = None
    try:
        idx = lines.index("소재지")
        result["주소명1"] = lines[idx + 1]
    except ValueError:
        result["주소명1"] = None
    try:
        idx = lines.index("지번주소")
        result["주소명2"] = lines[idx + 1]
    except ValueError:
        result["주소명2"] = None
    try:
        idx = lines.index("전화걸기")
        phone_numbers = []
        if idx + 1 < len(lines):
            phone_numbers.append(lines[idx + 1])
        if idx + 2 < len(lines) and lines[idx + 2] == "/":
            if idx + 3 < len(lines):
                phone_numbers.append(lines[idx + 3])
        result["일반전화"] = phone_numbers[0] if phone_numbers else None
        result["휴대전화"] = phone_numbers[1] if len(phone_numbers) > 1 else None
    except ValueError:
        result["일반전화"] = None
        result["휴대전화"] = None
    return result

def is_valid_phone(phone):
    return phone is not None and phone != "/"


def save_last_end_info(sido_code, sido_name, last_page):
    """
    현재 시도 코드(sido_code)와 시도 이름(sido_name), 마지막 페이지(last_page) 및 현재 타임스탬프를
    JSON 파일에 저장합니다.
    기존 파일이 있다면 해당 시도 코드에 대한 항목만 수정(업데이트)하고, 없으면 새 항목을 추가합니다.
    """
    # 현재 시각을 문자열로 변환 (예: "2023-10-10 15:30:25")
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_record = {
        "sido_name": sido_name,
        "last_page": last_page,
        "timestamp": timestamp
    }

    data = {}
    # 파일이 이미 존재하면 기존 데이터를 로드
    if os.path.exists(txt_filename):
        try:
            with open(txt_filename, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print("기존 데이터를 불러오는 중 오류 발생:", e)
            data = {}

    # 해당 시도 코드에 대해 새로운 값을 할당 (있으면 덮어쓰고, 없으면 추가)
    data[sido_code] = new_record

    # 업데이트된 데이터를 파일에 저장 (덮어쓰기)
    with open(txt_filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print(f"최종 정보가 저장되었습니다: {data[sido_code]}")


def get_last_end_info(sido_code):
    """
    txt_filename에 저장된 JSON 데이터에서 해당 시도(sido_code)의 마지막 처리 페이지를 반환합니다.
    데이터가 없으면 0을 반환합니다.
    """
    if os.path.exists(txt_filename):
        try:
            with open(txt_filename, "r", encoding="utf-8") as f:
                data = json.load(f)
                if sido_code in data:
                    return data[sido_code].get("last_page", 0)
        except Exception as e:
            print("Error reading last_end info:", e)
    return 0

if __name__ == "__main__":
    extract_and_print_all_links()
