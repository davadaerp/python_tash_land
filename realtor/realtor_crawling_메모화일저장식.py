import os
import requests
import time
from realtor_db_utils import realtor_save_to_sqlite
#
from config import REALTOR_DB_PATH

# 저장파일명
txt_filename = os.path.join(REALTOR_DB_PATH, "last_mem_no.txt")

def parse_realtor_info(text):
    # 줄바꿈 기준으로 공백 제거하며 분리
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    result = {}
    # 제목은 첫 번째 항목
    result["제목"] = lines[0]
    # 대표자: "대표자" 다음 항목
    try:
        idx = lines.index("대표자")
        result["대표자"] = lines[idx + 1]
    except ValueError:
        result["대표자"] = None
    # 소재지(주소명1): "소재지" 다음 항목
    try:
        idx = lines.index("소재지")
        result["주소명1"] = lines[idx + 1]
    except ValueError:
        result["주소명1"] = None
    # 지번주소(주소명2): "지번주소" 다음 항목
    try:
        idx = lines.index("지번주소")
        result["주소명2"] = lines[idx + 1]
    except ValueError:
        result["주소명2"] = None
    # 전화번호 처리:
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
    """전화번호가 None이 아니고 '/'가 아니라면 유효한 번호로 간주합니다."""
    return phone is not None and phone != "/"

def get_last_mem_no():
    """last_mem_no.txt 파일에서 마지막 mem_no 값을 정수로 반환합니다.
       파일이 없으면 0을 반환합니다."""
    if os.path.exists(txt_filename):
        try:
            with open(txt_filename, "r", encoding="utf-8") as f:
                last = f.read().strip()
                return int(last) if last.isdigit() else 0
        except:
            return 0
    else:
        return 0

def save_last_end(end):
    """최종 end 번호를 txt 파일에 저장합니다."""
    with open(txt_filename, "w", encoding="utf-8") as f:
        f.write(str(end))
    print(f"최종 mem_no({end})가 '{txt_filename}'에 저장되었습니다.")


def main():
    # last_mem_no.txt에서 마지막 mem_no를 읽어 시작 번호 결정 (없으면 0, 즉 1부터)
    last_mem = get_last_mem_no()
    start = last_mem + 1
    print(f"시작 mem_no: {start}")

    # 단위 설정 (예: 100개)
    process_unit = 30000
    end = start + process_unit - 1
    print(f"mem_no 범위: {start} ~ {end}")

    results = []
    BATCH_SIZE = 300  # 배치 저장 단위를 300건으로 설정

    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/90.0.4430.93 Safari/537.36")
    }

    # 한글 키를 영문 키로 변환하기 위한 매핑
    mapping = {
        "제목": "title",
        "대표자": "representative",
        "주소명1": "address1",
        "주소명2": "address2",
        "일반전화": "landline_phone",
        "휴대전화": "mobile_phone"
    }

    for mem in range(start, end + 1):
        mem_no = str(mem).zfill(7)
        url = f"https://www.karhanbang.com/office/office_detail.asp?topM=09&mem_no={mem_no}"
        try:
            response = requests.get(url, headers=headers, timeout=10)
        except Exception as e:
            print(f"mem_no {mem_no}: 요청 중 오류 발생 ({e})")
            continue

        if response.status_code != 200:
            print(f"mem_no {mem_no}: 페이지 요청 실패, 상태 코드: {response.status_code}")
            continue

        # BeautifulSoup을 이용해 HTML 파싱
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")
        info_div = soup.find("div", class_="realtorsInfoBig clearFix")
        if not info_div:
            print(f"mem_no {mem_no}: 중개사정보 영역을 찾을 수 없습니다.")
            continue

        extracted_text = info_div.get_text(separator="\n", strip=True)
        parsed_info = parse_realtor_info(extracted_text)
        parsed_info["mem_no"] = mem_no

        # 한글 키를 영문 키로 치환하여 새 딕셔너리 생성
        converted_info = {"mem_no": mem_no}
        for kor_key, eng_key in mapping.items():
            converted_info[eng_key] = parsed_info.get(kor_key)

        # 전화번호 유효성 검사 (일반전화 혹은 휴대전화 둘 중 하나라도 있으면 저장)
        if is_valid_phone(parsed_info.get("일반전화")) or is_valid_phone(parsed_info.get("휴대전화")):
            converted_info["landline_phone"] = parsed_info.get("일반전화")
            converted_info["mobile_phone"] = parsed_info.get("휴대전화")
            results.append(converted_info)
            print(f"mem_no {mem_no}: 정보 저장 완료.")
        else:
            print(f"mem_no {mem_no}: 전화번호 없음, 저장 안함.")

        # 배치 크기(BATCH_SIZE)만큼 결과가 쌓이면 데이터베이스에 저장
        if len(results) >= BATCH_SIZE:
            print(f"저장 전 현재 배치 건수: {len(results)} 건. 저장 수행...")
            realtor_save_to_sqlite(results)
            results = []  # 저장 후 리스트 초기화
            #
            save_last_end(mem)  # 현재 처리한 mem_no를 저장
            #
            time.sleep(3)  # 저장 후 약간의 대기

        time.sleep(0.5)

    if results:
        realtor_save_to_sqlite(results)
    else:
        print("저장할 데이터가 없습니다.")

    # 최종 end 번호를 txt 파일에 저장
    save_last_end(end)

if __name__ == "__main__":
    main()
