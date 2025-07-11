import time
import random
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import json
import re

from apt_db_utils import apt_save_to_csv, apt_save_to_sqlite, apt_drop_table

# 쿠키 정보 (필요에 따라 수정)
cookies = {
    '_ga': 'GA1.1.1084468181.1734915860',
    'NAC': 'bLinBcgL5eHAA',
    '_fwb': '92EW36MJWoMlKDFNRGVTar.1734916083966',
    'NNB': 'P3BVN6YZW5UGO',
    'landHomeFlashUseYn': 'Y',
    'nhn.realestate.article.rlet_type_cd': 'Z02',
    'page_uid': 'i33ygsqptbNsse1dgqZssssstQC-503024',
    'NACT': '1',
    'nid_inf': '175862896',
    'NID_AUT': 'ygKx/8S35QHdbpFvrSj6Ain0juNAFljR+cLAR9Xnk1ITOoT1SOkvRSxgY4GqlFk1',
    'NID_JKL': 'fBQoOPU3NBnyLC3PSsnyOMWne/GV1pCjtpoL/9zUcMA=',
    'NID_SES': 'AAABonCFzQxM5vkiE54OMdyMPbSrToEm9aTkHKImD1LkHzoK0N0MZFhf9oSp2Bb7vsW689gWf1In0Rt24iwlKHdtigcGIsJV7vd6iqk3uXwD46j8sNDbImEQD+zz4c8uO1mIpFKAcSKCx1wawnUp74WxJv3ZugmAhOuSmXUaE82g7bxQ7lnKzz0xZdt0NBUyiX6mkNxAFKvIECrIJlq3FeXkzJnLL2G1oDIQZp6h/Vyp+/lpTy6VlK4DHdIll8UXoh525cy/YVWmkzCXd0hklcleD/5va5YYj2eSN/rlSVz/YlvXUtZR4BAZBwU9RNpFVY9BnbvLNgZ56L7rwFm8CEW5TYwWd3+LMytkJp+1zXx2lyqRmNHloosAuT1MoRgWjf8CQkEQhl7wKzlU5CdcEfOVOqvNQalo2MRRJu8AcnG39BDNEvDAp5eVQwCSEWE1N7YcaqF1BKEn1vQjSB8IVwsR8VvNFKYMdSZ25jhmwz95JIVnaON1nqHR/1xWOohG4dx+VPp8m0wRpmNBpfzcl07o9G6p9a4C0nPIbGh37LwgOLiJhkCONpSHtzOPJ5UJEUNp4A==',
    '_ga_451MFZ9CFM': 'GS1.1.1736498640.8.0.1736498642.0.0.0',
    'REALESTATE': 'Fri%20Jan%2010%202025%2017%3A44%3A02%20GMT%2B0900%20(Korean%20Standard%20Time)',
    'BUC': 'DKN0WiwVKe4qzAXKCI07Dr9GJz7Gpi1vd5NL1wCoAWw=',
}

# 여러 User-Agent 문자열 목록
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_6_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPad; CPU OS 15_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/114.0.1823.67',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/109.0'
]


# 기본 헤더 템플릿 (매 요청마다 User-Agent를 무작위 선택)
BASE_HEADERS = {
    'accept': '*/*',
    'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    'authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IlJFQUxFU1RBVEUiLCJpYXQiOjE3MzY0OTg2NDIsImV4cCI6MTczNjUwOTQ0Mn0.g37w29EO_D45o3PXXHvTCtXMOJe6d50Q1zGwW1S_WoA',
    'cache-control': 'no-cache',
    'referer': 'https://new.land.naver.com/offices?ms=37.497624,127.107268,17&a=SG:SMS&e=RETAIL&articleNo=2464180374',
}

# 무료 프록시 서버 예시 (유효한 프록시 주소로 교체하세요)
PROXIES = [
    'http://152.26.229.52:9443',
    'http://149.129.255.179:80',
    'http://117.74.65.207:443'
]

def get_random_proxy():
    proxy = random.choice(PROXIES)
    return {
        'http': proxy,
        'https': proxy
    }

# 저장 방식 선택: "csv" 또는 "sqlite"
SAVE_MODE = "sqlite"  # 원하는 방식으로 변경 가능 (예: "csv")
BATCH_SIZE = 500     # 레코드 1000개마다 저장
PAGE_DELAY_SIZE = 5  # 5페이지당 딜레이 처리

# 전체삭제 후 크롤링 처리 여부
data_all_deletes = True

# 누적 저장된 레코드 건수
saved_count = 0

# 수집한 데이터 저장 리스트
data_entries = []

# 수정: 매매는 365일, 월세는 10일 기준으로 검색
recent_search_day_sale = 365 * 2
recent_search_day_rent = 365 * 2
today = datetime.today()

totPage = 1000
tradeType = "매매"  # 예시: 매매, 월세 등
#
areas = {
    "북변동": "4157010100",
    "운양동": "4157010300"
}
#
# areas = {
#     "북변동": "4157010100",
#     "걸포동": "4157010200",
#     "운양동": "4157010300",
#     "감정동": "4157010500",
#     "장기동": "4157010400",
#     "사우동": "4157010600",
#     "풍무동": "4157010700",
#     "마산동": "4157010800",
#     "구래동": "4157010900",
# }


# 법정코드 변환방식
# 위 코드에서 해당로우에 폐지라고 되어있는 부문과 4128700000 같은 코드에 뒷자리 5자리가 00000인것은 스킵하고 아래구조로 만들어줘.
# areas = {
#     "구산동": "2826012200",
#    "법곳동": "2826012200",
# }

# 날짜 형식 변환 함수 (YYYYMMDD → YYYY-MM-DD)
def format_date(date_str):
    if date_str and len(date_str) == 8:
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    return ""

# 세션 생성 및 기본 설정
session = requests.Session()
session.cookies.update(cookies)

def get_random_headers():
    headers = BASE_HEADERS.copy()
    headers['User-Agent'] = random.choice(USER_AGENTS)
    return headers

# 상세정보에 해당하는 내역을 가져옴.
def extract_next_data(url):
    headers = get_random_headers()
    response = session.get(url, headers=headers)
    if response.status_code != 200:
        print(f"웹페이지를 가져오지 못했습니다: {response.status_code}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    script_tag = soup.find("script", id="__NEXT_DATA__")
    if not script_tag:
        print("JSON 데이터가 포함된 스크립트 태그를 찾을 수 없습니다.")
        return None

    try:
        data = json.loads(script_tag.string)
        return data
    except json.JSONDecodeError as e:
        print("JSON 파싱 중 오류 발생:", e)
        return None

def extract_price_info_from_dehydrated_state(json_data):
    try:
        queries = json_data['props']['pageProps']['dehydratedState']['queries']
    except KeyError as e:
        print("dehydratedState 또는 queries를 찾을 수 없습니다:", e)
        return None

    for query in queries:
        try:
            result = query['state']['data']['result']
            if isinstance(result, dict) and 'priceInfo' in result:
                return result['priceInfo']
        except KeyError:
            continue

    print("priceInfo를 찾을 수 없습니다.")
    return None

def print_price_info(price_info):
    sale_deposit_price = convert_to_korean_amount(price_info.get("previousDeposit") / 10000) or 0
    sale_rent_price = price_info.get("previousMonthlyRent") // 10000 or 0
    return sale_deposit_price, sale_rent_price

def convert_to_korean_amount(amount):
    try:
        amount = int(amount)
    except Exception:
        return ""
    result = ""
    if amount >= 10000:
        eok = amount // 10000
        remainder = amount % 10000
        result = f"{eok}억"
        if remainder >= 1000:
            chun = remainder // 1000
            result += f"{chun}천"
    elif amount >= 1000:
        chun = amount // 1000
        remainder = amount % 1000
        result = f"{chun}천"
        if remainder >= 100:
            baek = remainder // 100
            result += f"{baek}백"
    elif amount >= 100:
        result = f"{amount // 100}백"
    else:
        result = str(amount)
    return result


def extract_active_third_components(filepath):
    """
    파일을 읽어들여
    1) 총 행 수
    2) 폐지여부가 '존재'인 행만 골라
    3) fullname.split() 했을 때 3번째 요소가 '동','읍','면','가'로 끝나면
       (code, third) 리스트로 반환
    """
    pattern = re.compile(r'.+(동|읍|면|리|가)$')
    extracted = []
    total = 0
    exist_count = 0
    abolished_count = 0

    with open(filepath, encoding='utf-8') as f:
        header = f.readline()  # 헤더 스킵
        for line in f:
            line = line.strip()
            if not line:
                continue
            total += 1
            parts = line.split('\t')
            if len(parts) != 3:
                continue
            code, fullname, status = parts

            if status == '존재':
                exist_count += 1
            elif status == '폐지':
                abolished_count += 1

            if status != '존재':
                continue

            # '존재'인 경우에만 마지막 토큰 검사
            name_tokens = fullname.split()
            if not name_tokens:
                continue
            last = name_tokens[-1]
            #print(last)
            if pattern.match(last):
                extracted.append((last, code, line))

    return total, exist_count, abolished_count, extracted


def main():
    global saved_count

    # 크롤링 시작 전 테이블 삭제 처리 (옵션)
    if data_all_deletes:
        apt_drop_table()
        print("apt 테이블을 삭제했습니다.")

    FILENAME = '주요투자법정동코드.txt'
    total, exist_cnt, abolished_cnt, results = extract_active_third_components(FILENAME)

    # 크롤링 시작
    for umdNm, cortarNo, line in results:
        for page in range(1, totPage):  # 페이지 1~99
            # APT:SG:SMS:GM : 상가,사무실,건물
            #url = f'https://new.land.naver.com/api/articles?cortarNo={cortarNo}&order=prcDesc&realEstateType=SG:SMS:GM%3ASMS&tradeType=월세&page={page}'
            url = f'https://new.land.naver.com/api/articles?cortarNo={cortarNo}&order=rank&realEstateType=APT:PRE&priceType=RETAIL&page={page}'
            headers = get_random_headers()
            response = session.get(url, headers=headers)
            #response = session.get(url, headers=headers, proxies={"https": get_random_proxy()})
            try:
                data = response.json()
                print(data)
            except json.JSONDecodeError:
                print("JSON 디코딩 오류 발생")
                continue

            article_list = data.get("articleList", [])
            # 만약 특정 페이지에서 article_list가 비어 있으면, 다음 umdNm, cortarNo로 넘어감.
            if not article_list:
                print(f"페이지 {page}에서 데이터 없음. {umdNm} ({cortarNo})에 대한 페이지 루프 종료.")
                break
            #==
            for article in article_list:
                confirm_date_str = format_date(article.get("articleConfirmYmd", ""))
                try:
                    article_date = datetime.strptime(confirm_date_str, "%Y-%m-%d")
                except ValueError:
                    continue

                # trade_type (매매/월세)를 가져와서 기준 날짜를 계산
                trade_type = article.get("tradeTypeName", "")
                if trade_type == "매매":
                    min_date_current = today - timedelta(days=recent_search_day_sale)
                elif trade_type == "월세":
                    min_date_current = today - timedelta(days=recent_search_day_rent)
                else:
                    # 기본값 처리 (예: 매매 기준)
                    min_date_current = today - timedelta(days=recent_search_day_sale)

                # 기준보다 오래된 데이터는 건너뜁니다.
                if article_date < min_date_current:
                    continue

                article_no = article.get("articleNo", "")
                article_name = article.get("articleName", "")
                real_estate_type = article.get("realEstateTypeName", "")
                article_real_estate_type = article.get("articleRealEstateTypeName", "")
                trade_type = article.get("tradeTypeName", "")
                price = article.get("dealOrWarrantPrc", "")
                rentPrc = article.get("rentPrc", "0")
                area1 = article.get("area1", 0)
                area2 = article.get("area2", 0)
                exclusive_area_pyeong = round(float(area2) * 0.3025, 1) if area2 else 0
                direction = article.get("direction", "방향 없음")
                buildingName = article.get("buildingName", "")
                floor_info = article.get("floorInfo", "").split("/")
                cfloor = floor_info[0] if len(floor_info) > 0 else ""
                tfloor = floor_info[1] if len(floor_info) > 1 else ""
                realtor_name = article.get("realtorName", "")
                company_name = article.get("cpName", "")
                article_url = article.get("cpPcArticleUrl", "")
                latitude = article.get("latitude", "")
                longitude = article.get("longitude", "")
                tag_list = f'"{", ".join(article.get("tagList", []))}"' if article.get("tagList", []) else ""
                feature_desc = f'"{article.get("articleFeatureDesc", "")}"' if article.get("articleFeatureDesc", "") else ""

                sale_deposit_price = 0
                sale_rent_price = 0
                # if trade_type == "매매":
                #     detail_url = "https://fin.land.naver.com/articles/" + article_no
                #     json_data = extract_next_data(detail_url)
                #     if json_data:
                #         price_info = extract_price_info_from_dehydrated_state(json_data)
                #         if price_info:
                #             sale_deposit_price, sale_rent_price = print_price_info(price_info)

                data_entry = {
                    "page": page,
                    "lawdCd":cortarNo[0:5],
                    "umdNm": umdNm,
                    "article_no": article_no,
                    "confirm_date_str": confirm_date_str,
                    "article_name": article_name,
                    "real_estate_type": real_estate_type,
                    "article_real_estate_type": article_real_estate_type,
                    "trade_type": trade_type,
                    "price": price,
                    "rentPrc": rentPrc,
                    "area1": area1,
                    "area2": area2,
                    "exclusive_area_pyeong": exclusive_area_pyeong,
                    "direction": direction,
                    "buildingName": buildingName,   # 동
                    "cfloor": cfloor,
                    "tfloor": tfloor,
                    "realtor_name": realtor_name,
                    "company_name": company_name,
                    "article_url": article_url,
                    "latitude": latitude,
                    "longitude": longitude,
                    "tag_list": tag_list,
                    "feature_desc": feature_desc,
                    "sale_deposit_price": sale_deposit_price,
                    "sale_rent_price": sale_rent_price
                }
                print(data_entry)
                data_entries.append(data_entry)

                # 일정 건수마다 저장 후 리스트 초기화
                if len(data_entries) >= BATCH_SIZE:
                    print(f"저장 전 현재까지 저장 건수: {saved_count + len(data_entries)} 건, 이번 배치: {len(data_entries)} 건")
                    if SAVE_MODE == "csv":
                        apt_save_to_csv(data_entries)
                    elif SAVE_MODE == "sqlite":
                        apt_save_to_sqlite(data_entries)
                    else:
                        print("알 수 없는 저장 방식입니다. SAVE_MODE 값을 'csv' 또는 'sqlite'로 설정해주세요.")
                    saved_count += len(data_entries)
                    data_entries.clear()
                    # 배치 저장 후 1~3초 사이의 랜덤 딜레이
                    time.sleep(random.uniform(1, 3))

            print(f"== 페이지 {page} 처리 완료 ==")
            # 페이지 처리 후, 페이지 번호가 PAGE_DELAY_SIZE의 배수일 때 딜레이 적용
            if page % PAGE_DELAY_SIZE == 0:
                delay = random.uniform(9, 15)
                print(f"== 페이지 {page} 처리 완료 (PAGE_DELAY_SIZE 배수), {delay:.2f}초 대기 ==")
                time.sleep(delay)

    # 남은 레코드 저장
    if data_entries:
        print(f"마지막 저장 전 현재까지 저장 건수: {saved_count + len(data_entries)} 건, 남은 배치: {len(data_entries)} 건")
        if SAVE_MODE == "csv":
            apt_save_to_csv(data_entries)
        elif SAVE_MODE == "sqlite":
            apt_save_to_sqlite(data_entries)
        else:
            print("알 수 없는 저장 방식입니다. SAVE_MODE 값을 'csv' 또는 'sqlite'로 설정해주세요.")
        saved_count += len(data_entries)
        data_entries.clear()

    print(f"총 저장 건수: {saved_count} 건")


if __name__ == '__main__':
    main()