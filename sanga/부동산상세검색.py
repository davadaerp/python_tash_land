import requests
from bs4 import BeautifulSoup
import json

def extract_next_data(url):
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/58.0.3029.110 Safari/537.3'
        )
    }
    response = requests.get(url, headers=headers)
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
    """
    json_data의 props.pageProps.dehydratedState.queries 배열 내에서
    state.data.result에 priceInfo가 포함된 객체를 찾아 반환합니다.
    """
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
    """
    price_info 내부의 각 필드를 필드명과 값으로 출력합니다.
    missing한 previousDeposit, previousMonthlyRent는 0으로 처리합니다.
    """
    # 키가 없거나 None이면 0으로 처리
    if price_info.get("previousDeposit") is None:
        price_info["previousDeposit"] = 0
    if price_info.get("previousMonthlyRent") is None:
        price_info["previousMonthlyRent"] = 0

    print("추출된 priceInfo 값:")
    for key, value in price_info.items():
        print(f"{key}: {value}")

if __name__ == '__main__':
    urls = [
        "https://fin.land.naver.com/articles/2509528434",
        "https://fin.land.naver.com/articles/2509505414"
    ]

    for url in urls:
        print(f"Processing URL: {url}")
        json_data = extract_next_data(url)
        if json_data:
            price_info = extract_price_info_from_dehydrated_state(json_data)
            if price_info:
                print_price_info(price_info)
        print("-" * 40)
